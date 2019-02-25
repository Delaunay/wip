
import json
from dgame.board.board import Board
from dgame.board.definition import BoardDefinitionFile
from dgame.power import Player
from dgame.board.unit import get_all_possible_move_orders, make_unit
from dgame.order import build
from dgame.order import hold, move, support_move, support, convoy_move, convoy, retreat, disband, build, waive

from diplomacy.engine.game import Game

from diplomacy.engine.actions.action_space import get_all_possible_move_orders as get_orders

import benchutils.call_graph as call_graph


def make_legacy_game(power, units):
    g = Game()
    g.clear_units()
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


def check_speed(g1, g2):
    import timeit

    def no_cache():
        g2.invalidate_cache()
        get_all_possible_move_orders(g2)

    def refactored():
        g2.invalidate_cache()
        get_orders(g2)
        #

    avg_old = sum(timeit.repeat(g1.get_all_possible_orders, repeat=20, number=20)) / (10 * 10)
    avg_new = sum(timeit.repeat(no_cache, repeat=20, number=20)) / (10 * 10)
    avg_ref = sum(timeit.repeat(refactored, repeat=20, number=20)) / (10 * 10)

    print('avg_old {}'.format(avg_old))
    print('avg_new {}'.format(avg_new))
    print('avg_ref {}'.format(avg_ref))
    print()
    print('Speedup {}'.format(avg_old / avg_new))
    print('Speedup {}'.format(avg_old / avg_ref))

    with call_graph.make_callgraph('no_cache_get_all_actors', '0', dry_run=False):
        no_cache()

    with call_graph.make_callgraph('cached_get_all_actors', '0', dry_run=False):
        refactored()


def compare(g1, g2, loc):
    r1 = list(g1.get_all_possible_orders(loc))
    r2 = list(map(lambda x: str(x), get_all_possible_move_orders(g2)[g2.get_tile_by_name(loc)]))

    diff = set(r1).symmetric_difference(set(r2))

    r1.sort()
    r2.sort()

    if diff:
        for i in r1:
            print(i)

        print('-')
        for i in r2:
            print(i)

        print('-')
        print(diff)
        print('-')


def test_via():
    """
        Test basic convoy mechanic
        A YOR -> NTH -> (BEL, DEN, EDI, HOL, LON, NWY)
        A YOR -> NTH -> NWY -> CLY
    """
    g1 = make_legacy_game('ENGLAND', ['A YOR', 'F NTH', 'F NWG'])
    g2 = make_new_game('ENGLAND', ['A YOR', 'F NTH', 'F NWG'])

    compare(g1, g2, 'YOR')

    check_speed(g1, g2)


def test_via2():
    """
        Test basic convoy mechanic
        A YOR -> NTH -> (BEL, DEN, EDI, HOL, LON, NWY)
        A YOR -> NTH -> NWY -> CLY
    """
    g1 = make_legacy_game('ENGLAND', ['A YOR', 'F NTH', 'F NWG'])
    g2 = make_new_game('ENGLAND', ['A YOR', 'F NTH', 'F NWG'])

    compare(g1, g2, 'YOR')

    check_speed(g1, g2)


test_via()
test_via2()
