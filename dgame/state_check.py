import json
from dgame.board import Board
from dgame.definition import BoardDefinitionFile
from dgame.power import Player
from dgame.unit import get_all_possible_move_orders, make_unit
from dgame.order import build
from dgame.province import Province
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

            for tile, paths in unit.reachable_tiles().items():
                print('     - ', tile, list(map(lambda x: x.short, tile.seas)))
            print('-' * 80)

            # raise AssertionError()

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

    def to_string(self, dest):
        if dest is None:
            return dest
        a = list(map(lambda x: str(x), dest))
        a.sort()
        return a

    def show_reachable(self, loc):
        print('>' * 10, 'REACHABLE (loc=', loc, ')')
        loc: Province = self.new_game.get_tile_by_name(loc)
        unit = self.new_game.get_unit_at(loc)

        if unit is None:
            return

        print(unit)
        for tile, paths in unit.reachable_tiles().items():
            print('   ->', str(tile), 'path=', tuple(map(lambda x: str(tuple(map(lambda y: str(y), x))), paths)))

        print('Adjacent Tiles')
        for n in loc.neighbours:
            print('   ->', n)

        print('<' * 10)

    def show_loc_diff(self, loc, old, new):
        print('>' * 10, 'DIFF (loc=', loc, ')')
        oldr = old.get(loc)
        newr = self.to_string(new.get(self.new_game.get_tile_by_name(loc)))

        if newr is not None:
            newr.sort()

        if oldr is not None:
            oldr.sort()

        print('OLD {}:'.format(loc), oldr)
        print()
        print('NEW {}:'.format(loc), newr)
        print('--')

        if newr is not None:
            print('   DIFF: ', set(oldr).symmetric_difference(newr))

        print('<' * 10)

    def show_move_orders(self, orders, loc):
        print('>' * 10, 'MOVE ORDER IN (loc=', loc, ')')
        ord = orders.get(self.new_game.get_tile_by_name(loc))

        if ord is None:
            return

        for o in ord:
            print(o)
        print('<' * 10)

    def replay(self, count=1):

        for k, round in enumerate(self.phases):
            print('=' * 80)
            s, y, p = split_name(round['name'])

            if p == 'M':
                state = round['state']
                # Set new game in function of cache

                self.new_game = self.make_new_game(state)
                move_orders = {}
                new_results = get_all_possible_move_orders(self.new_game, move_orders)
                old_results = self.old_game.get_all_possible_orders()

                old_units = []
                new_units = []

                for unit in self.new_game.units():
                    new_units.append('{:>30} {}'.format(unit.owner.power[0], unit))

                for name, p in self.old_game.powers.items():
                    for u in p.units:
                        old_units.append('{:>30} {}'.format(name, u))

                old_units.sort()
                new_units.sort()

                print('{:>30}      {:>30} k={}'.format('OLD', 'NEW', k), len(old_units), len(new_units))
                print('-' * 80)
                for o, n in zip(old_units, new_units):
                    print(o, n)
                print('-' * 80)

                self.show_move_orders(move_orders, 'BUL')

                self.show_reachable('CON')

                self.show_loc_diff('CON', old_results, new_results)

                compare_results(old_results, new_results, self.new_game)


            else:
                print('Skipping: {}'.format(p))

            orders = round['orders']
            results = round['results']

            # Check if all the orders that are going to be executed were found
            for power, orders in orders.items():
                self.old_game.set_orders(power, orders)

            # All have been processed
            self.old_game.process()
            phase = self.old_game._phase_abbr()

            if k >= count:
                break

            print(orders)
            print(results)

            # F NWG C A YOR - EDI
            # F NTH C A YOR - EDI
            # A YOR - EDI VIA


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    game = GameExecutor('/home/user1/diplomacy/diplomacy/tests/network/1.json')

    print(game.replay(12))
