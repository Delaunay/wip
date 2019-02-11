# pylint: skip-file

import timeit

from diplomacy_research.utils.proto import dict_to_proto
from diplomacy_research.proto.diplomacy_proto.game_pb2 import State as StateProto
import diplomacy_research.benchmarks.sample_messages as message

from benchutils.report import print_stat_streams
from benchutils.versioning import get_git_version


def message_proto(repeat=40, number=40):
    """ benchmark message transform from dict to proto"""
    messages = [
        message.message_message,
        message.phase_history_message,
        message.possible_orders_message,
        message.state_message,
        message.saved_game_message,
        message.long_saved_game,
        message.config_message
    ]

    for fun in messages:
        dict, proto = fun()

        time = sum(timeit.repeat(lambda: dict_to_proto(dict, proto), repeat=repeat, number=number)) / number

        print('{:>30}: {:10.4f} s | {:10.4f} message/s'.format(fun.__name__, time, 1 / (time / number)))

    print('-' * 80)


state_dict = {
    'game_id': '12345',
    'name': 'S1901M',
    'map': 'standard',
    'zobrist_hash': '1234567890',
    'note': 'Note123',
    'rules': ['R2', 'R1'],
    'units': {'AUSTRIA': ['A PAR', 'A MAR'], 'FRANCE': ['F AAA', 'F BBB']},
    'centers': {'AUSTRIA': ['PAR', 'MAR'], 'FRANCE': ['AAA', 'BBB'], 'ENGLAND': []},
    'influence': {'AUSTRIA': ['x1', 'x2']},
    'civil_disorder': {'FRANCE': 0, 'ENGLAND': 1},
    'homes': {'AUSTRIA': ['PAR1', 'MAR1'], 'FRANCE': ['AAA1', 'BBB1']},
    'builds': {
        'AUSTRIA': {'count': 0, 'homes': []},
        'FRANCE': {'count': -1, 'homes': []},
        'RUSSIA': {'count': 2, 'homes': ['PAR', 'MAR']}
    },
    'board_state': [1, 2, 3, 4, 5, 6, 7, 8],
    'context': {
        'FRANCE': [1.1, 1.2, 1.3],
        'ENGLAND': [2.1, 2.2, 2.3]
    }
}


def test_to_proto():
    """ test generic proto to dict conversion """
    return dict_to_proto(state_dict, StateProto)


def test_direct():
    """ test direct insertion into a proto"""
    state = StateProto()
    state.game_id = '12345'
    state.name = 'S1901M'
    state.map = 'standard'
    state.zobrist_hash = '1234567890'
    state.note = 'Note123'

    state.rules.extend(['R2', 'R1'])
    state.units['AUSTRIA'].value.extend(['A PAR', 'A MAR'])
    state.units['FRANCE'].value.extend(['F AAA', 'F BBB'])
    state.centers['AUSTRIA'].value.extend(['PAR', 'MAR'])
    state.centers['FRANCE'].value.extend(['AAA', 'BBB'])
    state.centers['ENGLAND'].value.extend([])
    state.influence['AUSTRIA'].value.extend(['x1', 'x2'])

    state.civil_disorder['FRANCE'] = 0
    state.civil_disorder['ENGLAND'] = 1

    state.homes['AUSTRIA'].value.extend(['PAR1', 'MAR1'])
    state.homes['FRANCE'].value.extend(['AAA1', 'BBB1'])
    state.builds['AUSTRIA'].count = 0
    state.builds['AUSTRIA'].homes.extend([])
    state.builds['AUSTRIA'].count = -1
    state.builds['AUSTRIA'].homes.extend([])
    state.builds['AUSTRIA'].count = 2

    state.builds['AUSTRIA'].homes.extend(['PAR', 'MAR'])
    state.board_state.extend([1, 2, 3, 4, 5, 6, 7, 8])
    state.context['FRANCE'].value.extend([1.1, 1.2, 1.3])
    state.context['ENGLAND'].value.extend([2.1, 2.2, 2.3])

    return state


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    from diplomacy_research.proto.diplomacy_proto.game_pb2 import Message, PhaseHistory, State, SavedGame

    print('Timing per message types')
    message_proto(40, 40)

    dict_to_proto_time = sum(timeit.repeat(test_to_proto, repeat=100, number=30))
    proto_direct_time = sum(timeit.repeat(test_direct, repeat=100, number=30))

    print('Time dict_to_proto: {:.4f}'.format(dict_to_proto_time))
    print('Time proto direct: {:.4f}'.format(proto_direct_time))

    print('-' * 80)

    msg = message.phase_history_message()[0]

    new_proto_time = sum(timeit.repeat(lambda: dict_to_proto(msg, PhaseHistory), repeat=100, number=30))

    print('Time new dict_to_proto (PhaseHistory): {:.4f}'.format(new_proto_time))

    import diplomacy_research.utils.proto as proto

    import diplomacy
    import diplomacy_research

    diplomacy_version, version_date = get_git_version(diplomacy)
    research_version, research_date = get_git_version(diplomacy_research)

    # print_stat_streams(
    #     ['[M]Message', '[M]History', '[M]Orders', '[M]State', '[M]Save', '[T]Total'],
    #     [proto.message_time, proto.history_time, proto.orders_time, proto.state_time, proto.save_time,
    #      proto.total_time],
    #     additional_names=['Diplomacy Version', 'Version Date', 'research'],
    #     additional_cols=[diplomacy_version, version_date, research_version],
    #     file_name='data/profile_proto.csv'
    # )
    sys.exit(0)



