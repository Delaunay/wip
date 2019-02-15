import json
from dgame.board import Board
from dgame.definition import BoardDefinitionFile
from dgame.power import Player
from dgame.unit import get_all_possible_move_orders, make_unit
from dgame.order import build
from dgame.order import hold, move, support_move, support, convoy_move, convoy, retreat, disband, build, waive

from diplomacy.engine.game import Game


def split_name(name):
    return name[0], name[1:-1], name[-1]


def compare_results(oldallr, newallr, board):
    oldallrall = []
    newallrall = []

    diff_n = 0
    old_tn = 0
    new_tn = 0

    items = list(newallr.items())
    items.sort(reverse=True)

    for (k, j) in items:

        i = oldallr.get(str(k))

        oldallrall.extend(i)
        newallrall.extend(j)

        old_set = set(i)
        new_set = set(list(map(lambda x: str(x), j)))

        diff = old_set.symmetric_difference(new_set)
        old_n = len(old_set)
        new_n = len(new_set)
        old_tn += len(old_set)
        new_tn += len(new_set)

        if old_n != new_n or diff:
            print(k, old_n, new_n)
            print('OLD  ', old_set)
            print('NEW  ', new_set)
            print('DIFF ', diff)

            unit = board.get_unit_at(board.get_tile_by_name(str(k)))
            print('-' * 80)
            print(unit, list(map(lambda x: x.short, unit.loc.neighbours)))
            for tile, path in unit.reachable_tiles():
                print('     - ', tile, list(map(lambda x: x.short, tile.seas)))
            print('-' * 80)

            raise AssertionError()

        if diff:
            #print(k, diff)
            diff_n += len(diff)

    print('-' * 80)
    print('OLD: ', len(oldallrall), old_tn)
    print('NEW: ', len(newallrall), new_tn)
    print('Diff ', diff_n)
    print('Diff ', old_tn - new_tn)
    print('-' * 80)


class GameExecutor:
    def make_new_game(self, state):
        diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
        players = [
            Player(p) for p in diplo_board.initial_condition()
        ]

        board = Board(diplo_board, players)

        for power, units in state['units'].items():
            p = board.get_player(power)
            for unit in units:
                a, b = unit.split(' ')

                board.process_order(p, build(make_unit(a, board.get_tile_by_name(b))))

        return board

    def __init__(self, file_name):
        self.game_replay = json.load(open(file_name, 'r'))
        self.phases = self.game_replay['phases']

        self.new_game = None
        self.old_game = Game()

    def replay(self, count=1):

        for k, round in enumerate(self.phases):
            s, y, p = split_name(round['name'])

            state = round['state']
            # Set new game in function of cache

            self.new_game = self.make_new_game(state)
            new_results = get_all_possible_move_orders(self.new_game)
            old_results = self.old_game.get_all_possible_orders()

            for unit in self.new_game.units():
                print('{:>30} {}'.format(unit.owner.power[0], unit))

            compare_results(old_results, new_results, self.new_game)

            orders = round['orders']
            results = round['results']

            # Check if all the orders that are going to be executed were found
            for power, orders in orders.items():
                self.old_game.set_orders(power, orders)

            # All have been processed
            self.old_game.process()

            if k >= count:
                break


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    game = GameExecutor('/home/user1/diplomacy/diplomacy/tests/network/1.json')

    print(game.replay(1))
