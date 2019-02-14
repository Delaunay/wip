from dgame.province import Province
from dgame.power import Player
from dgame.order import Order
from dgame.order import move, hold, support, support_move, convoy, convoy_move, build, disband
from dgame.order import MOVE
from dgame.diplomacy_europe_1901 import Diplomacy1901

from enum import IntEnum, unique
from typing import Set, List


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

    def get_possible_move_order(self, orders_per_location=None, move_orders=None) -> Set[Order]:
        """ All possible order during the move phase """
        tiles = self.reachable_tiles()

        orders = {hold(self)}

        if move_orders is None:
            move_orders = {}

        def move_unit(unit: Unit, dest: Province):
            order = move(unit, dest=dest)
            orders.add(order)

            if tile not in move_orders:
                move_orders[tile] = set()

            move_orders[tile].add(order)

        # first we establish where can a unit move
        # then given that information we can check where multiple units can move to the same location and add the
        # support move order

        for tile in tiles:
            #other_orders = None

            #if orders_per_location is not None:
            #    other_orders = orders_per_location.get(tile)

            sup_unit = self.board.get_unit_at(tile)

            # no unit so we can move right away
            if sup_unit is None or not sup_unit.is_fleet:
                move_unit(self, tile)

            if sup_unit is not None:
                orders.add(support(self, target=sup_unit))

                # if both units can move into a tile then do a support_move
                # common_tiles = set(tiles).intersection(sup_unit.reachable_tiles())
                # common_tiles.discard(self.loc)
                # common_tiles.discard(sup_unit.loc)

                # for dest in common_tiles:
                #    orders.add(support_move(self, sup_unit, dest))

                # There is a fleet unit which means we can convoy to a destination
                if not self.is_fleet and sup_unit.is_fleet:

                    # do not convoy to an adjacent tile (why take the boat if you can walk to it?)
                    if sup_unit.loc is not tile:
                        orders.add(convoy(sup_unit, target=self, dest=tile))
                        orders.add(convoy_move(self, dest=tile))
                    else:
                        move_unit(self, tile)

                # if a unit can move to the destination
                # if other_orders is not None:
                #     for order in other_orders:
                #        # we can support the attack move iff we can also move to it
                #        if order.order == MOVE and order.unit is not self and order.dest in self.loc.neighbours:
                #            orders.add(support_move(unit=self, target=order.unit, dest=order.dest))

        return orders

    def reachable_tiles(self):
        if self._reachable_tiles_cache is None:
            self._reachable_tiles_cache = self._reachable_tiles(False, [])

            # remove coasts BUL/EC, BUL/SC => BUL
            if not self.is_fleet:
                self._reachable_tiles_cache = set(
                    map(lambda x: self.board.get_tile_by_id(x.without_coast), self._reachable_tiles_cache))

        return self._reachable_tiles_cache

    def _reachable_tiles(self, convoy_: bool, path: List[Province]) -> Set[Province]:
        """ Compute all the reachable tiles for a given unit.
            This take into account all the adjacent land tiles and all the land tiles accessible through convoys """
        reachable = set()

        # For each tile check if they are accessible
        for tile_id in self.loc.neighbours:

            tile = self.board.get_tile_by_id(tile_id)

            if tile.is_water:
                unit = self.board.get_unit_at(tile)

                if unit is not None and unit.is_fleet:
                    # There is a fleet on the tile so we might be able to convoy though fleet chains
                    path.append(self.loc)
                    reachable = reachable.union(unit._reachable_tiles(convoy_=True, path=path))
            else:
                reachable.add(tile)

        # remove current location
        reachable.discard(self.loc)
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

        if not convoy_:
            # return set(filter(lambda x: self.board.get_tile_by_id(x).is_water, self.loc.neighbours))
            reachable = set()

            for tile_id in self.loc.neighbours:
                tile = self.board.get_tile_by_id(tile_id)

                if tile.is_water and tile not in path:
                    reachable.add(tile)

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


def get_all_possible_move_orders(board):
    other_orders = {}
    move_orders = {}

    for unit in board.units():
        other_orders[unit.loc] = unit.get_possible_move_order(other_orders, move_orders)

    for dest, orders in move_orders.items():

        for o1 in orders:
            unit = o1.unit
            corder = other_orders[unit.loc]

            for o2 in orders:
                if o1 is o2:
                    continue

                target = o2.unit
                corder.add(support_move(unit, target=target, dest=dest))

    return other_orders


if __name__ == '__main__':
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

    from diplomacy.engine.game import Game

    game = Game()
    #game.clear_units()
    #game.set_units('TURKEY', ['A NOR', 'F NTH'])

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

    orders = {}

    for p in players:
        power = p.power

        for (tp, loc) in power[3]:
            orders[loc] = board.process_order (p, build(make_unit(tp, board.get_tile_by_name(loc))))

    # board.add_unit(UnitType.Fleet, board.get_tile_by_name('NOR'), players[0])

    # bud = board.process_order(austria, build(make_unit(ARMY, board.get_tile_by_name('BUD'))))
    # board.process_order(austria, build(make_unit(ARMY, board.get_tile_by_name('VIE'))))
    # board.process_order(austria, build(make_unit(FLEET, board.get_tile_by_name('TRI'))))
    #
    # board.process_order(england, build(make_unit(ARMY, board.get_tile_by_name('LVP'))))
    # board.process_order(england, build(make_unit(FLEET, board.get_tile_by_name('LON'))))
    # board.process_order(england, build(make_unit(FLEET, board.get_tile_by_name('EDI'))))
    #
    # board.process_order(france, build(make_unit(ARMY, board.get_tile_by_name('MAR'))))
    # board.process_order(france, build(make_unit(ARMY, board.get_tile_by_name('PAR'))))
    # board.process_order(france, build(make_unit(FLEET, board.get_tile_by_name('BRE'))))
    #
    # board.process_order(germany, build(make_unit(ARMY, board.get_tile_by_name('MUN'))))
    # board.process_order(germany, build(make_unit(ARMY, board.get_tile_by_name('BER'))))
    # board.process_order(germany, build(make_unit(FLEET, board.get_tile_by_name('KIE'))))
    #
    # board.process_order(italy, build(make_unit(ARMY, board.get_tile_by_name('ROM'))))
    # board.process_order(italy, build(make_unit(ARMY, board.get_tile_by_name('VEN'))))
    # board.process_order(italy, build(make_unit(FLEET, board.get_tile_by_name('NAP'))))
    #
    # board.process_order(russia, build(make_unit(ARMY, board.get_tile_by_name('WAR'))))
    # board.process_order(russia, build(make_unit(ARMY, board.get_tile_by_name('MOS'))))
    # board.process_order(russia, build(make_unit(FLEET, board.get_tile_by_name('SEV'))))
    # board.process_order(russia, build(make_unit(FLEET, board.get_tile_by_name('STP'))))
    #
    # con = board.process_order(turkey, build(make_unit(ARMY, board.get_tile_by_name('CON'))))
    # board.process_order(turkey, build(make_unit(ARMY, board.get_tile_by_name('SMY'))))
    # board.process_order(turkey, build(make_unit(FLEET, board.get_tile_by_name('ANK'))))

    #other_orders = {}
    #for unit in board.units():
    #    other_orders[unit.loc] = unit.get_possible_move_order(other_orders)

    #new = list(map(lambda x: repr(x), con.get_possible_move_order(other_orders)))

    loc = 'MAR'

    new = get_all_possible_move_orders(board)[board.get_tile_by_name(loc)]
    new = list(map(lambda x: str(x), new))
    new.sort()

    old = list(set(game.get_all_possible_orders()[loc]))
    old.sort()

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

    for (k, j) in newallr.items():

        i = oldallr.get(str(k))

        oldallrall.extend(i)
        newallrall.extend(j)

        old_set = set(i)
        new_set = set(list(map(lambda x: repr(x), j)))
        diff = old_set.difference(new_set)

        if diff:
            print(k, diff)
            diff_n += len(diff)

    print('-' * 80)
    print('OLD: ', len(oldallrall))
    print('NEW: ', len(newallrall))
    print('Diff ', diff_n)

