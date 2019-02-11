# pylint: skip-file
import sys
from tqdm import tqdm
from diplomacy import Game
from diplomacy.utils.export import to_saved_game_format
import ujson as json
from diplomacy_research.models.state_space import extract_state_proto, extract_phase_history_proto, \
    extract_message_history_proto, extract_possible_orders_proto

import benchutils.call_graph as call_graph
from benchutils.chrono import chrono
from benchutils.statstream import StatStream
from benchutils.report import print_stat_streams
from benchutils.versioning import get_git_version

import time

game_time = StatStream(5)
state_time = StatStream(5)
history_time = StatStream(5)
message_time = StatStream(5)
orders_time = StatStream(5)
loop_time = StatStream(5)
process_time = StatStream(5)
save_time = StatStream(5)


def rerun_game(json_game):
    """ Replays an entire dgame in the dataset to profile engine performance """

    game = Game(map_name=json_game['map'], rules=json_game['rules'])

    g1 = time.time()

    for phase in json_game['phases']:
        a1 = time.time()
        _ = extract_state_proto(game)
        a2 = time.time()
        _ = extract_phase_history_proto(game)
        a3 = time.time()
        _ = extract_message_history_proto(game)
        a4 = time.time()
        _ = extract_possible_orders_proto(game)
        a5 = time.time()

        state_time.update(a2 - a1)
        history_time.update(a3 - a2)
        message_time.update(a4 - a3)
        orders_time.update(a5 - a4)

        a1 = time.time()
        for power_name, power_orders in phase['orders'].items():

            if not power_orders:
                continue

            if game.get_current_phase()[-1] == 'R':
                power_orders = [order.replace(' - ', ' R ') for order in power_orders]

            power_orders = [order for order in power_orders if order != 'WAIVE']

            game.set_orders(power_name, power_orders, expand=False)
        a2 = time.time()
        loop_time.update(a2 - a1)

        a1 = time.time()
        game.process()
        a2 = time.time()
        process_time.update(a2 - a1)

    game_time.update(time.time() - g1)

    s1 = time.time()
    _ = to_saved_game_format(game)
    save_time.update(time.time() - s1)


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
    call_graph.NO_CALL_GRAPHS = not args.call

    import diplomacy
    import diplomacy_research

    diplomacy_version, version_date = get_git_version(diplomacy)
    research_version, research_date = get_git_version(diplomacy_research)

    with call_graph.make_callgraph('profile_actor', '0', dry_run=not args.call):
        with open(args.data, 'r') as dataset_file:

            for game_id, line in enumerate(tqdm(dataset_file)):
                json_game = json.loads(line.rstrip('\n'))
                rerun_game(json_game)

                if game_id >= args.n:
                    break

    print('Report:')
    print_stat_streams(
        ['State', 'History', 'Message', 'Orders', 'Loop', 'Process', 'Game', 'Save'],
        [state_time, history_time, message_time, orders_time, loop_time, process_time, game_time, save_time],
        additional_names=['Diplomacy Version', 'Version Date', 'research'],
        additional_cols=[diplomacy_version, version_date, research_version],
        file_name='data/profile_actor.csv'
    )
    print('Done')

    import diplomacy_research.utils.proto as proto

    #print_stat_streams(
    #    ['[M]Message', '[M]History', '[M]Orders', '[M]State', '[M]Save', '[T]Total'],
    #    [proto.message_time, proto.history_time, proto.orders_time, proto.state_time, proto.save_time, proto.total_time],
    #    additional_names=['Diplomacy Version', 'Version Date', 'research'],
    #    additional_cols=[diplomacy_version, version_date, research_version],
    #    file_name='data/profile_actor.csv'
    #)
    sys.exit(0)


