#!/usr/bin/env python3
import logging
import os
from multiprocessing import Process
import shutil
import time
import zipfile

import gym
from diplomacy import Game
from tornado import gen, ioloop
from tqdm import tqdm

from diplomacy_research.models.datasets.grpc_dataset import GRPCDataset, ModelConfig
from diplomacy_research.models.gym.environment import DiplomacyEnv
from diplomacy_research.models.gym.wrappers import SaveGame, LimitNumberYears, RandomizePlayers, AutoDraw, LoopDetection
from diplomacy_research.models.policy.order_based import \
    PolicyAdapter as OrderPolicyAdapter, BaseDatasetBuilder as OrderBaseDatasetBuilder
from diplomacy_research.models.policy.token_based import \
    PolicyAdapter as TokenPolicyAdapter, BaseDatasetBuilder as TokenBaseDatasetBuilder
from diplomacy_research.models.self_play.reward_functions import DefaultRewardFunction
from diplomacy_research.models.message_space import add_message_tokens_to_saved_game
from diplomacy_research.models.state_space import extract_state_proto, extract_phase_history_proto, \
    extract_message_history_proto, extract_possible_orders_proto, add_cached_states_to_saved_game, \
    add_rewards_to_saved_game_proto, NB_POWERS, get_map_powers
from diplomacy_research.players import ModelBasedPlayer, RuleBasedPlayer
from diplomacy_research.players.rulesets import easy_ruleset
from diplomacy_research.proto.diplomacy_proto.game_pb2 import SavedGame as SavedGameProto
from diplomacy_research.utils.cluster import is_port_opened, kill_processes_using_port
from diplomacy_research.utils.process import start_tf_serving, download_file, kill_subprocesses_on_exit
from diplomacy_research.utils.proto import dict_to_proto, proto_to_bytes, proto_to_zlib
from diplomacy_research.settings import WORKING_DIR

LOGGER = logging.getLogger('diplomacy_research.scripts.launch_bot')
MODEL_URL = 'http://storage.googleapis.com/ppaquette-diplomacy/files/latest_model.zip'
PERIOD_SECONDS = 10
MAX_SENTINEL_CHECKS = 3
MAX_TIME_BETWEEN_CHECKS = 300
SERVING_PORT = 9500
NOISE = 0.
TEMPERATURE = 0.1
DROPOUT_RATE = 0.
USE_BEAM = False

def launch_serving():
    """ Launches or relaunches the TF Serving process """
    # Stop all serving child processes
    if is_port_opened(SERVING_PORT):
        kill_processes_using_port(SERVING_PORT)

    # Launching a new process
    log_file_path = os.path.join(WORKING_DIR, 'data', 'log_serving.txt')
    serving_process = Process(target=start_tf_serving,
                              args=(SERVING_PORT, WORKING_DIR),
                              kwargs={'force_cpu': True,
                                      'log_file_path': log_file_path})
    serving_process.start()
    kill_subprocesses_on_exit()

    # Waiting for port to be opened.
    for attempt_ix in range(90):
        time.sleep(10)
        if is_port_opened(SERVING_PORT):
            break
        LOGGER.info('Waiting for TF Serving to come online. - Attempt %d / %d', attempt_ix + 1, 90)
    else:
        LOGGER.error('TF Serving is not online after 15 minutes. Aborting.')
        raise RuntimeError()

    # Setting configuration
    new_config = ModelConfig(name='player', base_path='/work_dir/data/bot', version_policy=None)
    for _ in range(30):
        if GRPCDataset.set_config('localhost', SERVING_PORT, new_config):
            LOGGER.info('Configuration set successfully.')
            break
        time.sleep(5.)
    else:
        LOGGER.error('Unable to set the configuration file.')

@gen.coroutine
def check_serving(player):
    """ Makes sure the current serving process is still active, otherwise restarts it.
        :param player: A player object to query the server
    """
    game = Game()

    # Trying to check orders
    for _ in range(MAX_SENTINEL_CHECKS):
        orders = yield player.get_orders(game, 'FRANCE')
        if orders:
            return

    # Could not get orders x times in a row, restarting process
    LOGGER.warning('Could not retrieve orders from the serving process after %d attempts.', MAX_SENTINEL_CHECKS)
    LOGGER.warning('Restarting TF serving server.')
    launch_serving()

@gen.coroutine
def create_model_based_player(adapter_ctor, dataset_builder_ctor):
    """ Function to connect to TF Serving server and query orders """
    # Start TF Serving
    launch_serving()

    # Creating player
    grpc_dataset = GRPCDataset(hostname='localhost',
                               port=SERVING_PORT,
                               model_name='player',
                               signature=adapter_ctor.get_signature(),
                               dataset_builder=dataset_builder_ctor())
    adapter = adapter_ctor(grpc_dataset)
    player = ModelBasedPlayer(adapter,
                              noise=NOISE,
                              temperature=TEMPERATURE,
                              dropout_rate=DROPOUT_RATE,
                              use_beam=USE_BEAM)

    # Validating openings
    yield player.check_openings()

    # Returning player
    return player

@gen.coroutine
def create_player():
    """ Function to download the latest model and create a player """
    bot_directory = os.path.join(WORKING_DIR, 'data', 'bot')
    bot_model = os.path.join(bot_directory, 'latest_model.zip')
    shutil.rmtree(bot_directory, ignore_errors=True)
    os.makedirs(bot_directory, exist_ok=True)

    # Downloading model
    download_file(MODEL_URL, bot_model, force=False)

    # Unzipping file
    zip_ref = zipfile.ZipFile(bot_model, 'r')
    zip_ref.extractall(bot_directory)
    zip_ref.close()

    # Detecting model type
    if os.path.exists(os.path.join(bot_directory, 'order_based.txt')):
        LOGGER.info('Creating order-based player.')
        player = yield create_model_based_player(OrderPolicyAdapter, OrderBaseDatasetBuilder)

    elif os.path.exists(os.path.join(bot_directory, 'token_based.txt')):
        LOGGER.info('Creating token-based player.')
        player = yield create_model_based_player(TokenPolicyAdapter, TokenBaseDatasetBuilder)

    else:
        LOGGER.info('Creating rule-based player')
        player = RuleBasedPlayer(ruleset=easy_ruleset)

    # Returning
    return player


def create_gym_environment(players):
    """ Creates a gym environment """
    env = gym.make('DiplomacyEnv-v0')
    env = LimitNumberYears(env, max_nb_years=35)
    env = LoopDetection(env, threshold=3)
    env = AutoDraw(env)
    env = RandomizePlayers(env, players)
    env = SaveGame(env)
    return env

@gen.coroutine
def get_orders_with_details(player, state_proto, power_name, phase_history_proto, message_history_proto,
                            possible_orders_proto):
    """ Gets the orders (and the corresponding policy details) for the locs the power should play.
        :param state_proto: A `.proto.dgame.State` representation of the state of the dgame.
        :param power_name: The name of the power we are playing
        :param phase_history_proto: A list of `.proto.dgame.PhaseHistory`. This represents prev phases.
        :param message_history_proto: A list of `.proto.dgame.Message` representing msgs sent/rcvd during the phase.
        :param possible_orders_proto: A `proto.dgame.PossibleOrders` object representing possible order for each loc.
        :return: A tuple with
                1) The list of orders the power should play (e.g. ['A PAR H', 'A MAR - BUR', ...])
                2) The policy details ==> {'locs': [], 'tokens': [], 'log_probs': []}
    """
    if not state_proto.units[power_name].value:
        return [], None

    return (yield player.get_orders_details_with_proto(state_proto,
                                                       power_name,
                                                       phase_history_proto,
                                                       message_history_proto,
                                                       possible_orders_proto))


from diplomacy_research.benchmarks.statstream import StatStream
from diplomacy_research.benchmarks.chrono import MultiStageChrono
import time

game_time = MultiStageChrono([
    'init_gym',
    'generating',
    'policies',
    'orders',
    'output_formating'], 1)

game_steps = MultiStageChrono([
    'get_game_proto',
    'get_game_tasks',
    'get_orders',
    'for_each_player_submit',
    'store_orders',
    'step_process'], 10)

game_steps_stat = StatStream(0)


class DiplomacyEnvironment:
    def __init__(self, player):
        self.players = [player] * NB_POWERS
        self.env = self.make_environment()
        self.powers = sorted([power_name for power_name in get_map_powers(self.env.game.map)])
        self.context = None

        self.stored_policy_details = []
        self.stored_submitted_orders = []
        self.stored_possible_orders = []

    def make_environment(self):
        # Making sure we use the SavedGame wrapper to record the dgame
        env = create_gym_environment(self.players)
        wrapped_env = env
        while not isinstance(wrapped_env, DiplomacyEnv):
            if isinstance(wrapped_env, SaveGame):
                break
            wrapped_env = wrapped_env.env
        else:
            env = SaveGame(env)

        # Resetting env
        env.reset()
        return env

    @property
    def assigned_powers(self):
        return self.env.get_all_powers_name()

    @property
    def is_done(self):
        return self.env.is_done

    def get_state(self, ctx):
        return extract_state_proto(self.env.game, ctx)

    def get_round_history(self):
        return extract_phase_history_proto(self.env.game)

    def get_message_history(self):
        return extract_message_history_proto(self.env.game)

    def get_possible_orders(self):
        return extract_possible_orders_proto(self.env.game)

    def process(self, **kwargs):
        return self.env.process(**kwargs)

    def step(self, action):
        return self.env.step(action)

    def save_history(self, policy, orders, prossible_orders):
        self.stored_policy_details += [policy]
        self.stored_submitted_orders += [orders]
        self.stored_possible_orders += [prossible_orders]

    def get_game_history(self, reward_fn=None):
        if reward_fn is None:
            reward_fn = DefaultRewardFunction()

        # Retrieving saved dgame
        saved_game = self.env.get_saved_game()
        saved_game = add_cached_states_to_saved_game(saved_game)
        saved_game = add_message_tokens_to_saved_game(saved_game)

        # Adding policy details and rewriting orders (using submitted orders as opposed to processed orders)
        for phase, policy_details, submitted_orders in zip(saved_game['phases'],
                                                           self.stored_policy_details,
                                                           self.stored_submitted_orders):
            phase['policy'] = {}

            # Storing policy details and orders
            for power_name in self.powers:
                if power_name in policy_details and policy_details[power_name]:
                    phase['policy'][power_name] = policy_details[power_name]
                    phase['orders'][power_name] = submitted_orders[power_name]

        # Adding power assignments, done reason, and kwargs
        done_reason = ''
        if self.env.done_reason is not None:
            done_reason = self.env.done_reason.value

        saved_game['assigned_powers'] = self.assigned_powers
        saved_game['done_reason'] = done_reason
        saved_game['kwargs'] = {
            power_name: self.players[self.assigned_powers.index(power_name)].kwargs for power_name in self.powers
        }

        # Converting to proto, and adding rewards
        saved_game_proto = dict_to_proto(saved_game, SavedGameProto)
        saved_game_proto = add_rewards_to_saved_game_proto(saved_game_proto, reward_fn)

        # Adding possible orders
        for phase, possible_order_proto in zip(saved_game_proto.phases, self.stored_possible_orders):
            for loc in possible_order_proto:
                phase.possible_orders[loc].MergeFrom(possible_order_proto[loc])

        # Converting to correct format
        output = {
            'proto': lambda proto: proto,
            'zlib': proto_to_zlib,
            'bytes': proto_to_bytes
        }['bytes'](saved_game_proto)

        return output


class DiplomacyGame:
    def __init__(self, player):
        self.env = DiplomacyEnvironment(player)
        self.orders_with_details = [] * NB_POWERS

        self.round_id = 0
        self.context = None

    def run(self):
        while self.env.is_done:
            self.round()
            self.round_id += 1

    def round(self):
        state_proto = self.env.get_state(self.env.context)
        phase_history_proto = self.env.get_round_history()
        message_history_proto = self.env.get_message_history()
        possible_orders_proto = self.env.get_possible_orders()

        # For each power what is the next order to take
        for i, (player, pow_name) in enumerate(zip(self.env.players, self.env.assigned_powers)):
            self.orders_with_details[i] = yield get_orders_with_details(
                player,
                state_proto,
                pow_name,
                phase_history_proto,
                message_history_proto,
                possible_orders_proto
            )

        # Stepping through env, storing policy details and possible orders
        phase_submitted_orders = {}
        phase_policy_details = {}

        for power_name, (order, policy_details) in zip(self.env.assigned_powers, self.orders_with_details):
            phase_policy_details[power_name] = policy_details
            phase_submitted_orders[power_name] = order

            if order:
                self.env.step((power_name, order))

        # Storing before processing
        self.env.save_history(
            phase_policy_details,
            phase_submitted_orders,
            possible_orders_proto
        )

        self.env.process()
