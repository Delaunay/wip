import json
from dgame.board import Board
from dgame.definition import BoardDefinitionFile
from dgame.power import Player
from dgame.unit import get_all_possible_move_orders, make_unit
from dgame.order import build
from dgame.order import hold, move, support_move, support, convoy_move, convoy, retreat, disband, build, waive

from diplomacy.engine.game import Game


def parse_loc(locstr, board):
    locstr = locstr.strip()
    loc = locstr[0:3]

    if '/' in locstr:
        loc = locstr[0:6]
    return board.get_tile_by_name(loc)


def parse_army(army, board):
    return board.get_unit_at(parse_loc(army[1:], board))
    # return make_unit(army[0], board.get_tile_by_name(parse_loc(army[1:])))

# F STP/SC - BOT == A STP - BOT
def parse_order(order: str, board):
    if ' S ' in order:
        if '-' in order:
            a, b = order.split(' S ')
            b, c = b.split(' - ')
            return support_move(parse_army(a, board), parse_army(b, board), parse_loc(c, board))

        a, b = order.split(' S ')
        return support(parse_army(a, board), parse_army(b, board))

    if 'VIA' in order:
        a, b = order.split(' - ')
        return convoy_move(parse_army(a, board), parse_loc(b, board))

    if ' - ' in order:
        a, b = order.split(' - ')
        return move(parse_army(a, board), parse_loc(b, board))

    if ' C ' in order:
        a, b = order.split(' C ')
        b, c = b.split(' - ')
        return convoy(parse_army(a, board), parse_army(b, board), parse_loc(c, board))

    if ' B' in order:
        return build(parse_army(order[:-1], board))

    if ' D' in order:
        return disband(parse_army(order[:-1], board))

    if ' H' in order:
        return hold(parse_army(order[:-1], board))

    #if self.order is WAIVE:
    #    return 'WAIVE'


def split_name(name):
    return name[0], name[1:-1], name[-1]


def compare_results(oldallr, newallr, board):
    oldallrall = []
    newallrall = []

    diff_n = 0
    old_tn = 0
    new_tn = 0

    for (k, j) in newallr.items():

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
            for tile in unit.reachable_tiles():
                print('     - ', tile, list(map(lambda x: x.short, tile.seas)))
            print('-' * 80)

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
    def make_new_game(self):
        diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
        players = [
            Player(p) for p in diplo_board.initial_condition()
        ]

        board = Board(diplo_board, players)

        orders = {}
        for p in players:
            power = p.power

            for (tp, loc) in power[3]:
                orders[loc] = board.process_order(p, build(make_unit(tp, board.get_tile_by_name(loc))))

        return board

    def __init__(self, file_name):
        self.game_replay = json.load(open(file_name, 'r'))
        self.phases = self.game_replay['phases']

        self.new_game = self.make_new_game()
        self.old_game = Game()

    def replay(self):

        for k, round in enumerate(self.phases):
            s, y, p = split_name(round['name'])

            new_results = get_all_possible_move_orders(self.new_game)
            old_results = self.old_game.get_all_possible_orders()

            for unit in self.new_game.units():
                print('{:>30} {}'.format(unit.owner.power[0], unit))

            compare_results(old_results, new_results, self.new_game)

            state = round['state']
            orders = round['orders']
            results = round['results']

            norders_pending = []

            # Check if all the orders that are going to be executed were found
            for power, orders in orders.items():
                player = self.new_game.get_player(power)

                for order in orders:
                    norder = parse_order(order, self.new_game)

                    loc = str(norder.unit.loc)

                    if order not in old_results[loc]:
                        print('OLD NOT FOUND: ', order)

                    tile = self.new_game.get_tile_by_name(loc)

                    norders = new_results.get(tile)

                    if norders is None:
                        print(loc, tile)

                    norders = list(map(lambda x: str(x), norders))

                    if order not in norders:
                        print('NEW NOT FOUND', order)


                    result = results[str(norder.unit)]

                    if not result:
                        norders_pending.append((player, norder))

                    print('>> ORDER: {:>30} == {:<30} ==> {}'.format(order, str(norder), result))

                self.old_game.set_orders(power, orders)

            # need to sort orders in a way that can be executed
            g = 0
            while len(norders_pending) > 0:
                failed = []

                for p, o in norders_pending:
                    try:
                        self.new_game.process_order(p, o)
                    except AssertionError:
                        failed.append((p, o))
                        print(p.power[0], o)

                print('--')
                norders_pending = failed
                g += 1

                assert g < 10

            # All have been processed
            self.old_game.process()
            self.new_game.invalidate_cache()

            if k >= 2:
                break


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    game = GameExecutor('/home/user1/diplomacy/diplomacy/tests/network/1.json')

    print(game.replay())

