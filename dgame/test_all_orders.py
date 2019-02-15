
from diplomacy import Game
import json
from dgame.board import Board
from dgame.definition import BoardDefinitionFile
from dgame.power import Player
from dgame.unit import get_all_possible_move_orders, make_unit
from dgame.order import build
from dgame.order import hold, move, support_move, support, convoy_move, convoy, retreat, disband, build, waive

from diplomacy.engine.game import Game


def make_legacy_game(power, units):
    g = Game()
    g.set_units(power, units)

    return g


def make_new_game(power, units):
    def make_board():
        diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
        players = [
            Player(p) for p in diplo_board.initial_condition()
        ]

        board = Board(diplo_board, players)
        return board

    board = make_board()

    p = board.get_player(power)
    for unit in units:
        a, b = unit.split(' ')

        board.process_order(p, build(make_unit(a, board.get_tile_by_name(b))))

    return board


def test_via():
    g1 = make_legacy_game('ENGLAND', ['A YOR', 'F NTH'])
    g2 = make_new_game('ENGLAND', ['A YOR', 'F NTH'])

    r1 = list(g1.get_all_possible_orders('YOR'))
    r2 = list(map(lambda x: str(x), get_all_possible_move_orders(g2)[g2.get_tile_by_name('YOR')]))

    r1.sort()
    r2.sort()

    for i in r1:
        print(i)

    print('-')
    for i in r2:
        print(i)

    print('-')
    print(set(r1).symmetric_difference(set(r2)))

    import timeit

    avg_old = sum(timeit.repeat(g1.get_all_possible_orders, repeat=20, number=20)) / (10 * 10)
    avg_new = sum(timeit.repeat(lambda: get_all_possible_move_orders(g2), repeat=20, number=20)) / (10 * 10)

    print('-')
    print('avg_old {}'.format(avg_old))
    print('avg_new {}'.format(avg_new))
    print('Speedup {}'.format(avg_old / avg_new))




test_via()
