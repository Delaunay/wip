from dgame.province import Province
from dgame.power import Player
from dgame.order import Order
from dgame.order import move, hold, support, support_move, convoy, convoy_move, build, disband
from dgame.order import CONVOY_MOVE

from enum import IntEnum, unique
from typing import Set, List

from collections import Iterable


def flatten(a: Iterable) -> List[any]:
    if isinstance(a, Iterable):
        r = []
        for i in a:
            elem = flatten(i)
            r.extend(elem)
        return r
    return [a]


@unique
class UnitType(IntEnum):
    Army = 0
    Fleet = 1

    def __repr__(self):
        if self.value:
            return 'F'
        return 'A'

    def __str__(self):
        if self.value:
            return 'F'
        return 'A'


ARMY = UnitType.Army
FLEET = UnitType.Fleet


class Unit:
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        self.loc = loc
        self.owner = owner
        self.board = board
        self.unit_type = None
        self._reachable_tiles_cache = None

    def get_possible_move_order(self, move_orders=None) -> Set[Order]:
        """ All possible order during the move phase """
        tiles = self.reachable_tiles()

        orders = {hold(self)}

        if move_orders is None:
            move_orders = {}

        def append_move_order(tile, order):
            loc_nc = tile.without_coast

            if loc_nc not in move_orders:
                move_orders[loc_nc] = set()

            move_orders[loc_nc].add(order)

        # first we establish where can a unit move
        # then given that information we can check where multiple units can move to the same location and add the
        # support move order

        for tile, path in tiles:
            sup_unit = self.board.get_unit_at(tile)

            if len(path) == 1:
                order = move(self, dest=tile)
                orders.add(order)
                append_move_order(tile, order)

            elif tile is not self.loc:
                order = convoy_move(self, tile, path=tuple(flatten(path)))
                orders.add(order)
                append_move_order(tile, order)

            if sup_unit is not None:
                # we cannot support a unit that convoys us
                if len(path) == 1:
                    orders.add(support(self, target=sup_unit))

                # There is a fleet unit which means we can convoy to a destination
                if not self.is_fleet and sup_unit.is_fleet and self.loc.seas:

                    # do not convoy to an adjacent tile (why take the boat if you can walk to it?)
                    if sup_unit.loc is not tile:
                        orders.add(convoy(sup_unit, target=self, dest=tile))
                        orders.add(convoy_move(self, dest=tile, path=tuple(flatten(path))))

        return orders

    def reachable_tiles(self):
        if self._reachable_tiles_cache is None:
            self._reachable_tiles_cache = self._reachable_tiles(False, [self.loc])

            # remove coasts BUL/EC, BUL/SC => BUL
            if not self.is_fleet:
                self._reachable_tiles_cache = set(map(lambda x: (x[0].without_coast, x[1]), self._reachable_tiles_cache))

        return self._reachable_tiles_cache

    def _reachable_tiles(self, convoy_: bool, path: List[Province]) -> Set[Province]:
        """ Compute all the reachable tiles for a given unit.
            This take into account all the adjacent land tiles and all the land tiles accessible through convoys """
        reachable = set()
        ipath = tuple(path)

        # For each tile check if they are accessible
        for tile in self.loc.neighbours:

            if tile.is_water:
                unit = self.board.get_unit_at(tile)

                if unit is not None and unit.is_fleet and tile not in path:
                    # There is a fleet on the tile so we might be able to convoy though fleet chains
                    path.append(self.loc)
                    reachable = reachable.union(unit._reachable_tiles(convoy_=True, path=path))

            else:
                if tile not in path:
                    reachable.add((tile, ipath))

        # remove current location
        return reachable

    @property
    def is_fleet(self):
        return self.unit_type == UnitType.Fleet


class Army(Unit):

    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)
        self.unit_type = UnitType.Army

    def __repr__(self):
        return 'A {}'.format(self.loc)


class Fleet(Unit):
    """ Fleets are special units can be in a water tile and land tiles with coasts """
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)
        self.origin_sea = loc
        self.unit_type = UnitType.Fleet

    def __repr__(self):
        return 'F {}'.format(self.loc)

    def _reachable_tiles(self, convoy_: bool, path: List[Province]) -> Set[Province]:
        """ fleets can reach every tile that are adjacent """
        # print(convoy_)

        if not convoy_:
            # return set(filter(lambda x: self.board.get_tile_by_id(x).is_water, self.loc.neighbours))
            reachable = set()

            for tile in self.loc.neighbours:
                # for a tile to be reachable by a fleet it needs to be either water
                # or a land tile with a common sea between current loc and dest loc
                has_common_sea = self.loc in tile.seas or len(self.loc.seas.intersection(tile.seas)) > 0

                if (tile.is_water or has_common_sea) and tile not in path:
                    reachable.add((tile, tuple(path)))

            reachable.discard(self.loc)
            return reachable

        path.append(self.loc)
        return super()._reachable_tiles(convoy_=True, path=path)


def make_unit(type: UnitType, loc: Province, owner: Player = None, board: 'Board' = None) -> Unit:
    """ Unit Factory """

    if type == 'A':
        return Army(loc, owner, board)

    if type == 'F':
        return Fleet(loc, owner, board)

    if type == UnitType.Fleet:
        return Fleet(loc, owner, board)

    return Army(loc, owner, board)


def get_all_possible_move_orders(board, move_orders=None):
    other_orders = {}
    if move_orders is None:
        move_orders = {}

    for unit in board.units():
        other_orders[unit.loc.without_coast] = unit.get_possible_move_order(move_orders)

    # no coast destination so we can unify fleet on coast and army supporting that fleet
    for dest_nc, orders in move_orders.items():

        for o1 in orders:
            unit = o1.unit
            corder = other_orders[unit.loc.without_coast]

            for o2 in orders:
                if o1 is o2:
                    continue
                if o1.unit is o2.unit:
                    continue
                elif o1.order == CONVOY_MOVE:
                    # in a `convoy move` the move (o2.unit) can be supported
                    # but the one doing the move cannot support
                    # i.e o1 has to be

                    # F HOL S A YOR - BEL  (A YOR - BEL VIA NTH)
                    # but A YOR S F HOL - BEL is not possible
                    if o1.path is None and o2.path is not None:
                        target = o2.unit
                        corder.add(support_move(unit, target=target, dest=o2.dest))
                        print('HERE')
                        #print(o1, list(map(lambda x: str(x), o1.path)))
                else:
                    target = o2.unit
                    corder.add(support_move(unit, target=target, dest=o2.dest))

                    # http://web.inter.nl.net/users/L.B.Kruijswijk/#6.B
                    # 6.B.8 UPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE
                    if o2.dest is not dest_nc:
                        corder.add(support_move(unit, target=target, dest=dest_nc))

    return other_orders


def test():
    #game.clear_units()
    #game.set_units('TURKEY', ['A NOR', 'F NTH'])
    print('=' * 75)
    for i in range(1, 76):

        tile = board.get_tile_by_id(i)

        unittype = ARMY
        if tile.is_water:
            unittype = FLEET

        # unit = board.build_unit(players[0], unittype, tile, )
        unit = board.process_order(austria, build(make_unit(unittype, tile)))

        print(i, unit, unit.reachable_tiles(), ' == ', board.get_tile_by_id(i).neighbours)

        board.process_order(austria, disband(unit))

        assert len(players[0].units) == 0
        assert len(board._loc_unit) == 0
        assert len(board.units()) == 0

    # -------------------------------------------------------------------------------

    print('=' * 80)

    a1 = board.process_order(austria, build(make_unit(ARMY, board.get_tile_by_name('NWY'))))
    print(a1, a1.reachable_tiles())

    f1 = board.process_order(austria, build(make_unit(FLEET, board.get_tile_by_name('NTH'))))

    print(a1, a1.reachable_tiles())

    print('-' * 10)
    print(a1.get_possible_move_order())

    orders = []

    for key, value in game.get_all_possible_orders().items():
        orders.extend(value)

    for i in range(0, len(orders) // 3):
        print('{:4d} {:>30} {:>30} {:>30}'.format(i, orders[i * 3], orders[i * 3 + 1], orders[i * 3 + 2]))

    board.process_order(players[0], disband(a1))
    board.process_order(players[0], disband(f1))

    assert len(players[0].units) == 0
    assert len(board._loc_unit) == 0
    assert len(board.units()) == 0


def profile():
    from dgame.board import Board
    from dgame.definition import BoardDefinitionFile
    from benchutils.call_graph import make_callgraph

    diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
    players = [
        Player(p) for p in diplo_board.initial_condition()
    ]

    austria = players[0]

    board = Board(diplo_board, players)

    orders = {}

    for p in players:
        power = p.power

        for (tp, loc) in power[3]:
            orders[loc] = board.process_order(p, build(make_unit(tp, board.get_tile_by_name(loc))))

    with make_callgraph('get_all_new', id='1', dry_run=False):
        get_all_possible_move_orders(board)


if __name__ == '__main__':
    profile()

    from dgame.board import Board
    from dgame.definition import BoardDefinitionFile
    import sys
    sys.stderr = sys.stdout

    diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
    players = [
        Player(p) for p in diplo_board.initial_condition()
    ]

    austria = players[0]

    board = Board(diplo_board, players)


    from diplomacy.engine.game import Game

    game = Game()

    orders = {}

    for p in players:
        power = p.power

        for (tp, loc) in power[3]:
            orders[loc] = board.process_order(p, build(make_unit(tp, board.get_tile_by_name(loc))))

    loc = 'MOS'

    new = get_all_possible_move_orders(board)[board.get_tile_by_name(loc)]
    new = list(map(lambda x: str(x), new))
    new.sort()

    old = list(set(game.get_all_possible_orders()[loc]))
    old.sort()

    unit = board.get_unit_at(board.get_tile_by_name(loc))

    print('-' * 80)
    print(unit)
    for tile in unit.reachable_tiles():
        print(tile, tile.seas)

    print('-' * 80)
    print(board.get_tile_by_name(loc).neighbours)
    print('new ', new)
    print('old ', old)
    print('-' * 80)
    print(set(new).difference(set(old)))

    import timeit

    avg_old = sum(timeit.repeat(game.get_all_possible_orders, repeat=20, number=20)) / (10 * 10)
    avg_new = sum(timeit.repeat(lambda: get_all_possible_move_orders(board), repeat=20, number=20)) / (10 * 10)

    print('avg_old {}'.format(avg_old))
    print('avg_new {}'.format(avg_new))
    print('Speedup {}'.format(avg_old / avg_new))

    print('-' * 80)
    oldallr = game.get_all_possible_orders()
    newallr = get_all_possible_move_orders(board)

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
            print('---')

        if diff:
            #print(k, diff)
            diff_n += len(diff)

    print('-' * 80)
    print('OLD: ', len(oldallrall), old_tn)
    print('NEW: ', len(newallrall), new_tn)
    print('Diff ', diff_n)
    print('Diff ', old_tn - new_tn)




