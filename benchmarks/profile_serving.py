#!/usr/bin/env python3
# pylint: skip-file

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

import benchutils.call_graph as call_graph
from benchutils.chrono import chrono
from benchutils.statstream import StatStream
from benchutils.report import print_stat_streams
from benchutils.versioning import get_git_version
import time


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


all_game_time = StatStream(1)
simulation_time = StatStream(1)
orders_time = StatStream(10)
process_time = StatStream(10)
submit_time = StatStream(10)
store_time = StatStream(10)

@chrono
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


@chrono
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


@chrono
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
    player.check_openings()

    # Returning player
    return player


@chrono
def create_player():
    """ Function to download the latest model and create a player """
    bot_directory = os.path.join(WORKING_DIR, 'data', 'bot')
    bot_model = os.path.join(bot_directory, 'latest_model.zip')
    shutil.rmtree(bot_directory, ignore_errors=True)
    os.makedirs(bot_directory, exist_ok=True)

    # Downloading model
    download_file(MODEL_URL, bot_model, force=True)

    # Unzipping file
    zip_ref = zipfile.ZipFile(bot_model, 'r')
    zip_ref.extractall(bot_directory)
    zip_ref.close()

    # Detecting model type
    if os.path.exists(os.path.join(bot_directory, 'order_based.txt')):
        LOGGER.info('Creating order-based player.')
        player = create_model_based_player(OrderPolicyAdapter, OrderBaseDatasetBuilder)

    elif os.path.exists(os.path.join(bot_directory, 'token_based.txt')):
        LOGGER.info('Creating token-based player.')
        player = create_model_based_player(TokenPolicyAdapter, TokenBaseDatasetBuilder)

    else:
        LOGGER.info('Creating rule-based player')
        player = RuleBasedPlayer(ruleset=easy_ruleset)

    # Returning
    return player


@chrono
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





@gen.coroutine
def run_entire_game(player):
    """ Runs an entire dgame using the player """
    start = time.time()
    # Init
    # ------------------------------------
    players = [player] * NB_POWERS
    nb_players = len(players)
    assert nb_players == NB_POWERS
    reward_fn = DefaultRewardFunction()

    # Making sure we use the SavedGame wrapper to record the dgame
    env = create_gym_environment(players)
    wrapped_env = env

    while not isinstance(wrapped_env, DiplomacyEnv):
        if isinstance(wrapped_env, SaveGame):
            break
        wrapped_env = wrapped_env.env
    else:
        env = SaveGame(env)

    # Resetting env
    env.reset()

    # Variables
    powers = sorted([power_name for power_name in get_map_powers(env.game.map)])
    assigned_powers = env.get_all_powers_name()
    stored_policy_details = []
    stored_submitted_orders = []
    stored_possible_orders = []
    context = None

    # Generating
    # ------------------------------------
    with call_graph.make_callgraph('game_loop', 'all'):
        s1 = time.time()
        # >>>>>>>>>>>>>>>>>>>>>>>>>
        while not env.is_done:
            state_proto = extract_state_proto(env.game, context)
            phase_history_proto = extract_phase_history_proto(env.game)
            message_history_proto = extract_message_history_proto(env.game)
            possible_orders_proto = extract_possible_orders_proto(env.game)

            s2 = time.time()
            # Getting orders and policy details
            tasks = [(player,
                      state_proto,
                      pow_name,
                      phase_history_proto,
                      message_history_proto,
                      possible_orders_proto) for player, pow_name in zip(env.players, assigned_powers)]

            orders_with_details = yield [get_orders_with_details(*args) for args in tasks]
            orders_time.update(time.time() - s2)

            s3 = time.time()
            # Stepping through env, storing policy details and possible orders
            phase_submitted_orders = {}
            phase_policy_details = {}

            for power_name, order_details in zip(assigned_powers, orders_with_details):
                order, policy_details = order_details
                phase_policy_details[power_name] = policy_details
                phase_submitted_orders[power_name] = order
                if order:
                    env.step((power_name, order))

            submit_time.update(time.time() - s3)

            # Storing before processing
            s4 = time.time()
            stored_policy_details += [phase_policy_details]
            stored_submitted_orders += [phase_submitted_orders]
            stored_possible_orders += [possible_orders_proto]
            store_time.update(time.time() - s4)

            # Processing
            p1 = time.time()
            env.process()
            process_time.update(time.time() - p1)

        # <<<<<<<<<<<<<<<<<<<<<<<<<<
        simulation_time.update(time.time() - s1)

        # Retrieving saved dgame
        saved_game = env.get_saved_game()
        saved_game = add_cached_states_to_saved_game(saved_game)
        saved_game = add_message_tokens_to_saved_game(saved_game)

        # Adding policy details and rewriting orders (using submitted orders as opposed to processed orders)
        for phase, policy_details, submitted_orders in zip(saved_game['phases'],
                                                           stored_policy_details,
                                                           stored_submitted_orders):
            phase['policy'] = {}

            # Storing policy details and orders
            for power_name in powers:
                if power_name in policy_details and policy_details[power_name]:
                    phase['policy'][power_name] = policy_details[power_name]
                    phase['orders'][power_name] = submitted_orders[power_name]

        # Adding power assignments, done reason, and kwargs
        done_reason = env.done_reason.value if env.done_reason is not None else ''
        saved_game['assigned_powers'] = assigned_powers
        saved_game['done_reason'] = done_reason
        saved_game['kwargs'] = {power_name: players[assigned_powers.index(power_name)].kwargs for power_name in powers}

        # Converting to proto, and adding rewards
        saved_game_proto = dict_to_proto(saved_game, SavedGameProto)
        saved_game_proto = add_rewards_to_saved_game_proto(saved_game_proto, reward_fn)

        # Adding possible orders
        for phase, possible_order_proto in zip(saved_game_proto.phases, stored_possible_orders):
            for loc in possible_order_proto:
                phase.possible_orders[loc].MergeFrom(possible_order_proto[loc])

        # Converting to correct format
        output = {'proto': lambda proto: proto,
                  'zlib': proto_to_zlib,
                  'bytes': proto_to_bytes}['bytes'](saved_game_proto)

        # Returning
        all_game_time.update(time.time() - start)
        return output


@gen.coroutine
@chrono
def run_games_forever(args):
    """ Generates games forever for profiling """
    player = create_player()
    progress_bar = tqdm()

    k = 0
    with call_graph.make_callgraph('run_games_forever', 'all', dry_run=not args.call):
        while True:
            yield run_entire_game(player)
            k += 1

            if k > args.n:
                break

            progress_bar.update(1)


class GracefulKiller:
    """ Implement a signal handler as a class """

    kill_now = False

    def __init__(self):
        import signal
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        kill_processes_using_port(SERVING_PORT)


if __name__ == '__main__':
    import argparse
    import sys

    sys.stderr = sys.stdout

    parser = argparse.ArgumentParser()

    parser.add_argument('--data', default='/Tmp/user1/diplomacy/standard_press_with_msgs.jsonl', type=str,
        help='dataset used to simulate a diplomacy dgame')

    parser.add_argument('-n', default=250, type=int,
        help='Number of dgame simulated')

    parser.add_argument('-call', default=False, action='store_true',
        help='Generate Calls graphs')

    args = parser.parse_args()

    import diplomacy
    import diplomacy_research

    diplomacy_version, version_date = get_git_version(diplomacy)
    research_version, research_date = get_git_version(diplomacy_research)

    killer = GracefulKiller()
    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.run_sync(lambda: run_games_forever(args))

    except KeyboardInterrupt:
        LOGGER.error('Script interrupted.')

    kill_processes_using_port(SERVING_PORT)

    print('Report:')
    print_stat_streams(
        ['All Game', 'Simulation', 'Orders', 'Process', 'Submit', 'Store'],
        [all_game_time, simulation_time, orders_time, process_time, submit_time, store_time],
        additional_names=['Diplomacy Version', 'Version Date', 'research'],
        additional_cols=[diplomacy_version, version_date, research_version],
        file_name='data/profile_serving.csv'
    )
    print('Done')

    import diplomacy_research.utils.proto as proto

    # print_stat_streams(
    #     ['[M]Message', '[M]History', '[M]Orders', '[M]State', '[M]Save', '[T]Total'],
    #     [proto.message_time, proto.history_time, proto.orders_time, proto.state_time, proto.save_time, proto.total_time],
    #     additional_names=['Diplomacy Version', 'Version Date', 'research'],
    #     additional_cols=[diplomacy_version, version_date, research_version],
    #     file_name='data/profile_serving.csv'
    # )
    sys.exit(0)
