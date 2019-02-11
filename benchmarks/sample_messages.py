# pylint: skip-file

import numpy as np
from diplomacy import Game
from diplomacy_research.proto.tensorflow_serving.apis.model_management_pb2 import ReloadConfigRequest
from diplomacy_research.proto.diplomacy_proto.common_pb2 import MapStringList
from diplomacy_research.proto.diplomacy_proto.game_pb2 import Message, PhaseHistory, State, SavedGame
from diplomacy_research.models.state_space import token_to_ix, get_order_tokens, TOKENS_PER_ORDER
from diplomacy_research.utils.proto import dict_to_proto, proto_to_dict


def message_message():
    message_dict = {'sender': 'FRANCE',
                    'recipient': 'ENGLAND',
                    'time_sent': 1548195276340776,
                    'phase': 'S1901M',
                    'message': 'Test Message',
                    'tokens': [1, 2, 3, 4, 5, 6]}
    return message_dict, Message


def phase_history_message():
    policy_1 = {'locs': ['PAR', 'MAR'],
                'tokens': [token_to_ix(order_token) for order_token in
                           get_order_tokens('A PAR H <EOS> <PAD> <PAD> <PAD> A MAR - PIE <EOS> <PAD> <PAD>')],
                'log_probs': np.random.rand(2 * TOKENS_PER_ORDER).tolist()}
    policy_2 = {'locs': ['xPAR', 'xMAR'],
                'tokens': [token_to_ix(order_token) for order_token in
                           get_order_tokens('A PAR H <EOS> <PAD> <PAD> <PAD> A MAR - PIE <EOS> <PAD> <PAD>')],
                'log_probs': np.random.rand(2 * TOKENS_PER_ORDER).tolist()}
    possible_orders = Game().get_all_possible_orders()

    phase_history_dict = {
        'name': 'S1902M',
        'state': {
            'game_id': '12345',
            'name': 'S1902M',
            'map': 'standard',
            'zobrist_hash': '1234567890',
            'note': 'Note123',
            'rules': ['R2', 'R1'],
            'units': {'AUSTRIA': ['A PAR', 'A MAR'], 'FRANCE': ['F AAA', 'F BBB']},
            'centers': {'AUSTRIA': ['PAR', 'MAR'], 'FRANCE': ['AAA', 'BBB'], 'ENGLAND': []},
            'homes': {'AUSTRIA': ['PAR1', 'MAR1'], 'FRANCE': ['AAA1', 'BBB1']},
            'builds': {'AUSTRIA': {'count': 0, 'homes': []},
                       'FRANCE': {'count': -1, 'homes': []},
                       'RUSSIA': {'count': 2, 'homes': ['PAR', 'MAR']}},
            'board_state': [10, 11, 12, 13, 14, 15, 16, 17],
            'context': {'FRANCE': [1.1, 1.2, 1.3],
                        'ENGLAND': [2.1, 2.2, 2.3]}},
        'orders': {'FRANCE': ['A PAR H', 'A MAR - BUR'],
                   'ENGLAND': []},
        'results': {'A PAR': [''], 'A MAR': ['bounce']},
        'messages': [
            {'time_sent': 0, 'sender': 'FRANCE', 'recipient': 'AUSTRIA', 'phase': 'S1901M', 'message': 'hello'},
            {'time_sent': 1, 'sender': 'AUSTRIA', 'recipient': 'FRANCE', 'phase': 'S1901M', 'message': 'salut'},
        ],

        'policy': {'FRANCE': policy_1,
                   'ENGLAND': policy_2},
        'prev_orders_state': [1, 2, 3, 4, 5, 6, 7, 8],
        'state_value': {'FRANCE': 2.56, 'ENGLAND': 6.78},
        'possible_orders': possible_orders
    }
    return phase_history_dict, PhaseHistory


def possible_orders_message():

    game = Game()
    possible_orders = game.get_all_possible_orders()
    return possible_orders, MapStringList


def state_message():

    state_dict = {'game_id': '12345',
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
                  'builds': {'AUSTRIA': {'count': 0, 'homes': []},
                             'FRANCE': {'count': -1, 'homes': []},
                             'RUSSIA': {'count': 2, 'homes': ['PAR', 'MAR']}},
                  'board_state': [1, 2, 3, 4, 5, 6, 7, 8],
                  'context': {'FRANCE': [1.1, 1.2, 1.3],
                              'ENGLAND': [2.1, 2.2, 2.3]}}
    return state_dict, State


def saved_game_message():

    game = Game()
    state_1 = {'game_id': '12345',
               'name': 'S1901M',
               'map': 'standard',
               'zobrist_hash': '1234567890',
               'note': 'Note123',
               'rules': ['R2', 'R1'],
               'units': {'AUSTRIA': ['A PAR', 'A MAR'], 'FRANCE': ['F AAA', 'F BBB']},
               'centers': {'AUSTRIA': ['PAR', 'MAR'], 'FRANCE': ['AAA', 'BBB'], 'ENGLAND': []},
               'homes': {'AUSTRIA': ['PAR1', 'MAR1'], 'FRANCE': ['AAA1', 'BBB1']},
               'builds': {'AUSTRIA': {'count': 0, 'homes': []},
                          'FRANCE': {'count': -1, 'homes': []},
                          'RUSSIA': {'count': 2, 'homes': ['PAR', 'MAR']}},
               'board_state': [1, 2, 3, 4, 5, 6, 7, 8],
               'context': {'FRANCE': [1.1, 1.2, 1.3],
                           'ENGLAND': [2.1, 2.2, 2.3]}}
    state_2 = {'game_id': 'x12345',
               'name': 'xS1901M',
               'map': 'xstandard',
               'zobrist_hash': '0987654321',
               'note': 'xNote123',
               'rules': ['xR2', 'xR1'],
               'units': {'AUSTRIA': ['xA PAR', 'xA MAR'], 'FRANCE': ['xF AAA', 'xF BBB']},
               'centers': {'AUSTRIA': ['xPAR', 'xMAR'], 'FRANCE': ['xAAA', 'xBBB'], 'ENGLAND': []},
               'homes': {'AUSTRIA': ['xPAR1', 'xMAR1'], 'FRANCE': ['xAAA1', 'xBBB1']},
               'builds': {'AUSTRIA': {'count': 0, 'homes': []},
                          'FRANCE': {'count': -1, 'homes': []},
                          'RUSSIA': {'count': 2, 'homes': ['xPAR', 'xMAR']}}}
    policy_1 = {'locs': ['PAR', 'MAR'],
                'tokens': [token_to_ix(order_token) for order_token in
                           get_order_tokens('A PAR H <EOS> <PAD> <PAD> <PAD> A MAR - PIE <EOS> <PAD> <PAD>')],
                'log_probs': np.random.rand(2 * TOKENS_PER_ORDER).tolist()}

    policy_2 = {'locs': ['xPAR', 'xMAR'],
                'tokens': [token_to_ix(order_token) for order_token in
                           get_order_tokens('A PAR H <EOS> <PAD> <PAD> <PAD> A MAR - PIE <EOS> <PAD> <PAD>')],
                'log_probs': np.random.rand(2 * TOKENS_PER_ORDER).tolist()}

    message_1 = {'sender': 'FRANCE', 'recipient': 'ENGLAND', 'time_sent': 100, 'phase': 'S1901M', 'message': 'Test 1'}
    message_2 = {'sender': 'ENGLAND', 'recipient': 'FRANCE', 'time_sent': 200, 'phase': 'S1901M', 'message': 'Test 2'}
    message_3 = {'sender': 'FRANCE', 'recipient': 'ENGLAND', 'time_sent': 300, 'phase': 'xS1901M', 'message': 'xTest 1'}
    message_4 = {'sender': 'ENGLAND', 'recipient': 'FRANCE', 'time_sent': 400, 'phase': 'xS1901M', 'message': 'xTest 2'}

    possible_orders = game.get_all_possible_orders()

    saved_game = {'id': '12345',
                  'map': 'standard',
                  'rules': ['R2', 'R1'],
                  'phases': [{'name': 'S1901M',
                              'state': state_1,
                              'orders': {'FRANCE': ['A PAR H', 'A MAR - PIE'],
                                         'ENGLAND': []},
                              'results': {},
                              'messages': [message_1, message_2],
                              'policy': {'FRANCE': policy_1, 'ENGLAND': policy_2},
                              'prev_orders_state': [10, 11, 12, 13, 14, 15],
                              'state_value': {'FRANCE': 5.67, 'ENGLAND': 6.78},
                              'possible_orders': possible_orders},

                             {'name': 'xS1901M',
                              'state': state_2,
                              'orders': {'FRANCE': ['xA PAR H', 'xA MAR - PIE'],
                                         'ENGLAND': []},
                              'results': {},
                              'messages': [message_3, message_4],
                              'policy': {'FRANCE': policy_2, 'ENGLAND': None}}],
                  'done_reason': 'auto_draw',

                  'assigned_powers': ['FRANCE', 'ENGLAND'],
                  'players': ['rule', 'v0'],
                  'kwargs': {'FRANCE': {'player_seed': 1, 'noise': 0.2, 'temperature': 0.3, 'dropout_rate': 0.4},
                             'ENGLAND': {'player_seed': 6, 'noise': 0.7, 'temperature': 0.8, 'dropout_rate': 0.9}},

                  'is_partial_game': True,
                  'start_phase_ix': 2,

                  'reward_fn': 'default_reward',
                  'rewards': {'FRANCE': [1.1, 2.2, 3.3],
                              'ENGLAND': [1.2, 2.3, 3.4]},
                  'returns': {'FRANCE': [11.1, 12.2, 13.3],
                              'ENGLAND': [11.2, 12.3, 13.4]}}

    return saved_game, SavedGame


def config_message():
    model_config = {
        'config': {
            'model_config_list': {
                'config': [
                    {'name': 'player', 'base_path': '/work_dir/data/bot', 'model_platform': 'tensorflow'}
                ]
            }
        }
    }
    return model_config, ReloadConfigRequest


def long_saved_game():
    msg = {
        'id': '12345',
        'map': 'standard',
        'rules': ['R2', 'R1'],
        'phases': [{
            'name': 'S1901M',
            'state': {
                'game_id': '12345',
                'name': 'S1901M',
                'map': 'standard',
                'zobrist_hash': '1234567890',
                'note': 'Note123',
                'rules': ['R2', 'R1'],
                'units': {
                    'AUSTRIA': ['A PAR', 'A MAR'],
                    'FRANCE': ['F AAA', 'F BBB']
                },
                'centers': {
                    'AUSTRIA': ['PAR', 'MAR'],
                    'FRANCE': ['AAA', 'BBB'],
                    'ENGLAND': []
                },
                'homes': {
                    'AUSTRIA': ['PAR1', 'MAR1'],
                    'FRANCE': ['AAA1', 'BBB1']
                },
                'builds': {
                    'AUSTRIA': {
                        'count': 0,
                        'homes': []
                    },
                    'FRANCE': {
                        'count': -1,
                        'homes': []
                    },
                    'RUSSIA': {
                        'count': 2,
                        'homes': ['PAR', 'MAR']
                    }
                },
                'board_state': [1, 2, 3, 4, 5, 6, 7, 8],
                'context': {
                    'FRANCE': [1.1, 1.2, 1.3],
                    'ENGLAND': [2.1, 2.2, 2.3]
                }
            },
            'orders': {
                'FRANCE': ['A PAR H', 'A MAR - PIE'],
                'ENGLAND': []
            },
            'results': {},
            'messages': [{
                'sender': 'FRANCE',
                'recipient': 'ENGLAND',
                'time_sent': 100,
                'phase': 'S1901M',
                'message': 'Test 1'
            }, {
                'sender': 'ENGLAND',
                'recipient': 'FRANCE',
                'time_sent': 200,
                'phase': 'S1901M',
                'message': 'Test 2'
            }],
            'policy': {
                'FRANCE': {
                    'locs': ['PAR', 'MAR'],
                    'tokens': [130, 14, 2, 0, 0, 0, 124, 68, 2, 0, 0],
                    'log_probs': [0.3359934095181816, 0.7826954654995362, 0.37325731700976694, 0.043439035660762126,
                                  0.10155457994723127, 0.9078561411209471, 0.5710751365075463, 0.0766560215797103,
                                  0.3376254298925716, 0.04016836642847732]
                },
                'ENGLAND': {
                    'locs': ['xPAR', 'xMAR'],
                    'tokens': [130, 14, 2, 0, 0, 0, 124, 68, 2, 0, 0],
                    'log_probs': [0.6107619631426755, 0.7978573233397326, 0.4577429241867229, 0.8034385278361997,
                                  0.15944257942114992, 0.9399266565086609, 0.09482979642944467, 0.2535088721946446,
                                  0.7538858740234038, 0.1999706729245243]
                }
            },
            'prev_orders_state': [10, 11, 12, 13, 14, 15],
            'state_value': {
                'FRANCE': 5.67,
                'ENGLAND': 6.78
            },
            'possible_orders': {
                'ADR': [],
                'AEG': [],
                'ALB': [],
                'ANK': ['F ANK H', 'F ANK - ARM', 'F ANK - CON', 'F ANK S A CON', 'F ANK - BLA', 'F ANK S F SEV - ARM',
                        'F ANK S A SMY - ARM', 'F ANK S A SMY - CON', 'F ANK S F SEV - BLA'],
                'APU': [],
                'ARM': [],
                'BAL': [],
                'BAR': [],
                'BEL': [],
                'BER': ['A BER H', 'A BER - MUN', 'A BER S A MUN', 'A BER - SIL', 'A BER - KIE', 'A BER S F KIE',
                        'A BER - PRU', 'A BER S A WAR - SIL', 'A BER S A MUN - SIL', 'A BER S A MUN - KIE',
                        'A BER S A WAR - PRU'],
                'BLA': [],
                'BOH': [],
                'BOT': [],
                'BRE': ['F BRE H', 'F BRE - GAS', 'F BRE - MAO', 'F BRE - PIC', 'F BRE - ENG', 'F BRE S A PAR - GAS',
                        'F BRE S A MAR - GAS', 'F BRE S A PAR - PIC', 'F BRE S F LON - ENG'],
                'BUD': ['A BUD H', 'A BUD - VIE', 'A BUD S A VIE', 'A BUD - GAL', 'A BUD - SER', 'A BUD - RUM',
                        'A BUD - TRI', 'A BUD S F TRI', 'A BUD S A VIE - GAL', 'A BUD S A WAR - GAL',
                        'A BUD S F SEV - RUM', 'A BUD S A VIE - TRI', 'A BUD S A VEN - TRI'],
                'BUL/EC': [],
                'BUL/SC': [],
                'BUL': [],
                'BUR': [],
                'CLY': [],
                'CON': ['A CON H', 'A CON - BUL', 'A CON - ANK', 'A CON S F ANK', 'A CON - SMY', 'A CON S A SMY',
                        'A CON S A SMY - ANK'],
                'DEN': [],
                'EAS': [],
                'EDI': ['F EDI H', 'F EDI - YOR', 'F EDI - NTH', 'F EDI - NWG', 'F EDI - CLY', 'F EDI S A LVP - YOR',
                        'F EDI S F LON - YOR', 'F EDI S F LON - NTH', 'F EDI S A LVP - CLY'],
                'ENG': [],
                'FIN': [],
                'GAL': [],
                'GAS': [],
                'GRE': [],
                'HEL': [],
                'HOL': [],
                'ION': [],
                'IRI': [],
                'KIE': ['F KIE H', 'F KIE - BAL', 'F KIE - DEN', 'F KIE - HEL', 'F KIE - HOL', 'F KIE - BER',
                        'F KIE S A BER', 'F KIE S A MUN - BER'],
                'LON': ['F LON H', 'F LON - WAL', 'F LON - ENG', 'F LON - YOR', 'F LON - NTH', 'F LON S A LVP - WAL',
                        'F LON S F BRE - ENG', 'F LON S A LVP - YOR', 'F LON S F EDI - YOR', 'F LON S F EDI - NTH'],
                'LVN': [],
                'LVP': ['A LVP H', 'A LVP - YOR', 'A LVP - CLY', 'A LVP - WAL', 'A LVP - EDI', 'A LVP S F EDI',
                        'A LVP S F LON - YOR', 'A LVP S F EDI - YOR', 'A LVP S F EDI - CLY', 'A LVP S F LON - WAL'],
                'LYO': [],
                'MAO': [],
                'MAR': ['A MAR H', 'A MAR - GAS', 'A MAR - PIE', 'A MAR - SPA', 'A MAR - BUR', 'A MAR S A PAR - GAS',
                        'A MAR S F BRE - GAS', 'A MAR S A VEN - PIE', 'A MAR S A PAR - BUR', 'A MAR S A MUN - BUR'],
                'MOS': ['A MOS H', 'A MOS - LVN', 'A MOS - WAR', 'A MOS S A WAR', 'A MOS - SEV', 'A MOS S F SEV',
                        'A MOS S F STP/SC', 'A MOS - UKR', 'A MOS - STP', 'A MOS S A WAR - LVN',
                        'A MOS S F STP/SC - LVN', 'A MOS S A WAR - UKR'],
                'MUN': ['A MUN H', 'A MUN - TYR', 'A MUN - RUH', 'A MUN - SIL', 'A MUN - KIE', 'A MUN S F KIE',
                        'A MUN - BOH', 'A MUN - BUR', 'A MUN - BER', 'A MUN S A BER', 'A MUN S A VIE - TYR',
                        'A MUN S A VEN - TYR', 'A MUN S A WAR - SIL', 'A MUN S A BER - SIL', 'A MUN S A BER - KIE',
                        'A MUN S A VIE - BOH', 'A MUN S A PAR - BUR', 'A MUN S A MAR - BUR', 'A MUN S F KIE - BER'],
                'NAF': [],
                'NAO': [],
                'NAP': ['F NAP H', 'F NAP - ION', 'F NAP - ROM', 'F NAP S A ROM', 'F NAP - TYS', 'F NAP - APU',
                        'F NAP S A VEN - ROM', 'F NAP S A ROM - APU', 'F NAP S A VEN - APU'],
                'NWY': [],
                'NTH': [],
                'NWG': [],
                'PAR': ['A PAR H', 'A PAR - PIC', 'A PAR - BUR', 'A PAR - GAS', 'A PAR - BRE', 'A PAR S F BRE',
                        'A PAR S F BRE - PIC', 'A PAR S A MUN - BUR', 'A PAR S A MAR - BUR', 'A PAR S A MAR - GAS',
                        'A PAR S F BRE - GAS'],
                'PIC': [],
                'PIE': [],
                'POR': [],
                'PRU': [],
                'ROM': ['A ROM H', 'A ROM - NAP', 'A ROM S F NAP', 'A ROM - TUS', 'A ROM - VEN', 'A ROM S A VEN',
                        'A ROM - APU', 'A ROM S A VEN - TUS', 'A ROM S F TRI - VEN', 'A ROM S F NAP - APU',
                        'A ROM S A VEN - APU'],
                'RUH': [],
                'RUM': [],
                'SER': [],
                'SEV': ['F SEV H', 'F SEV - ARM', 'F SEV - BLA', 'F SEV - RUM', 'F SEV S F ANK - ARM',
                        'F SEV S A SMY - ARM', 'F SEV S F ANK - BLA', 'F SEV S A BUD - RUM'],
                'SIL': [],
                'SKA': [],
                'SMY': ['A SMY H', 'A SMY - ARM', 'A SMY - SYR', 'A SMY - ANK', 'A SMY S F ANK', 'A SMY - CON',
                        'A SMY S A CON', 'A SMY S F SEV - ARM', 'A SMY S F ANK - ARM', 'A SMY S A CON - ANK',
                        'A SMY S F ANK - CON'],
                'SPA/NC': [],
                'SPA/SC': [],
                'SPA': [],
                'STP/NC': [],
                'STP/SC': ['F STP/SC H', 'F STP/SC - LVN', 'F STP/SC - FIN', 'F STP/SC - BOT', 'F STP/SC S A WAR - LVN',
                           'F STP/SC S A MOS - LVN'],
                'STP': ['F STP/SC H', 'F STP/SC - LVN', 'F STP/SC - FIN', 'F STP/SC - BOT', 'F STP/SC S A WAR - LVN',
                        'F STP/SC S A MOS - LVN'],
                'SWE': [],
                'SYR': [],
                'TRI': ['F TRI H', 'F TRI - ADR', 'F TRI - ALB', 'F TRI - VEN', 'F TRI S A VEN', 'F TRI S A ROM - VEN'],
                'TUN': [],
                'TUS': [],
                'TYR': [],
                'TYS': [],
                'UKR': [],
                'VEN': ['A VEN H', 'A VEN - TYR', 'A VEN - PIE', 'A VEN - TUS', 'A VEN - ROM', 'A VEN S A ROM',
                        'A VEN - TRI', 'A VEN S F TRI', 'A VEN - APU', 'A VEN S A VIE - TYR', 'A VEN S A MUN - TYR',
                        'A VEN S A MAR - PIE', 'A VEN S A ROM - TUS', 'A VEN S F NAP - ROM', 'A VEN S A VIE - TRI',
                        'A VEN S A BUD - TRI', 'A VEN S F NAP - APU', 'A VEN S A ROM - APU'],
                'VIE': ['A VIE H', 'A VIE - TYR', 'A VIE - GAL', 'A VIE - BOH', 'A VIE - BUD', 'A VIE S A BUD',
                        'A VIE - TRI', 'A VIE S F TRI', 'A VIE S A MUN - TYR', 'A VIE S A VEN - TYR',
                        'A VIE S A WAR - GAL', 'A VIE S A BUD - GAL', 'A VIE S A MUN - BOH', 'A VIE S A BUD - TRI',
                        'A VIE S A VEN - TRI'],
                'WAL': [],
                'WAR': ['A WAR H', 'A WAR - LVN', 'A WAR - GAL', 'A WAR - SIL', 'A WAR - MOS', 'A WAR S A MOS',
                        'A WAR - UKR', 'A WAR - PRU', 'A WAR S F STP/SC - LVN', 'A WAR S A MOS - LVN',
                        'A WAR S A VIE - GAL', 'A WAR S A BUD - GAL', 'A WAR S A MUN - SIL', 'A WAR S A BER - SIL',
                        'A WAR S A MOS - UKR', 'A WAR S A BER - PRU'],
                'WES': [],
                'YOR': [],
                'SWI': []
            }
        }, {
            'name': 'xS1901M',
            'state': {
                'game_id': 'x12345',
                'name': 'xS1901M',
                'map': 'xstandard',
                'zobrist_hash': '0987654321',
                'note': 'xNote123',
                'rules': ['xR2', 'xR1'],
                'units': {
                    'AUSTRIA': ['xA PAR', 'xA MAR'],
                    'FRANCE': ['xF AAA', 'xF BBB']
                },
                'centers': {
                    'AUSTRIA': ['xPAR', 'xMAR'],
                    'FRANCE': ['xAAA', 'xBBB'],
                    'ENGLAND': []
                },
                'homes': {
                    'AUSTRIA': ['xPAR1', 'xMAR1'],
                    'FRANCE': ['xAAA1', 'xBBB1']
                },
                'builds': {
                    'AUSTRIA': {
                        'count': 0,
                        'homes': []
                    },
                    'FRANCE': {
                        'count': -1,
                        'homes': []
                    },
                    'RUSSIA': {
                        'count': 2,
                        'homes': ['xPAR', 'xMAR']
                    }
                }
            },
            'orders': {
                'FRANCE': ['xA PAR H', 'xA MAR - PIE'],
                'ENGLAND': []
            },
            'results': {},
            'messages': [{
                'sender': 'FRANCE',
                'recipient': 'ENGLAND',
                'time_sent': 300,
                'phase': 'xS1901M',
                'message': 'xTest 1'
            }, {
                'sender': 'ENGLAND',
                'recipient': 'FRANCE',
                'time_sent': 400,
                'phase': 'xS1901M',
                'message': 'xTest 2'
            }],
            'policy': {
                'FRANCE': {
                    'locs': ['xPAR', 'xMAR'],
                    'tokens': [130, 14, 2, 0, 0, 0, 124, 68, 2, 0, 0],
                    'log_probs': [0.6107619631426755, 0.7978573233397326, 0.4577429241867229, 0.8034385278361997,
                                  0.15944257942114992, 0.9399266565086609, 0.09482979642944467, 0.2535088721946446,
                                  0.7538858740234038, 0.1999706729245243]
                },
                'ENGLAND': None
            }
        }],
        'done_reason': 'auto_draw',
        'assigned_powers': ['FRANCE', 'ENGLAND'],
        'players': ['rule', 'v0'],
        'kwargs': {
            'FRANCE': {
                'player_seed': 1,
                'noise': 0.2,
                'temperature': 0.3,
                'dropout_rate': 0.4
            },
            'ENGLAND': {
                'player_seed': 6,
                'noise': 0.7,
                'temperature': 0.8,
                'dropout_rate': 0.9
            }
        },
        'is_partial_game': True,
        'start_phase_ix': 2,
        'reward_fn': 'default_reward',
        'rewards': {
            'FRANCE': [1.1, 2.2, 3.3],
            'ENGLAND': [1.2, 2.3, 3.4]
        },
        'returns': {
            'FRANCE': [11.1, 12.2, 13.3],
            'ENGLAND': [11.2, 12.3, 13.4]
        }
    }

    return msg, SavedGame
