from dgame.province import Province
from dgame.power import Player
from dgame.order import Order, move, hold, support, convoy
from dgame.diplomacy_europe_1901 import Diplomacy1901

from enum import IntEnum, unique
from typing import Set


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


class Unit:
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        self.loc = loc
        self.owner = owner
        self.board = board
        self.unit_type = None

    def get_possible_order(self) -> Set[Order]:
        tiles = self.reachable_tiles()

        orders = {hold(self)}

        for tile in tiles:
            sup_unit = self.board.get_unit(tile)
            if sup_unit is not None:
                orders.add(support(self, tile))

                # There is a fleet unit which means we can convoy
                if self.is_fleet and sup_unit.is_fleet:
                    orders.add(convoy(self, tile))
            else:
                orders.add(move(self, tile))

        return orders

    def reachable_tiles(self, convoy_=False) -> Set[Province]:
        """ Compute all the reachable tiles for a given unit. This take into account all the adjacent land tiles
                    and all the land tiles accessible through convoys """
        reachable = set()

        # For each tile check if they are accessible
        for tile_id in self.loc.neighbours:

            tile = self.board.get_tile_by_id(tile_id)

            if tile.is_water:
                unit = self.board.get_unit(tile)

                if unit is not None and unit.is_fleet:
                    # There is a fleet on the tile so we might be able to convoy though fleet chains
                    reachable = reachable.union(unit.reachable_tiles(convoy_=True))
            else:
                reachable.add(tile)

        # remove current location
        reachable.discard(self.loc)
        return reachable

    def disband(self):
        self.owner.units.remove(self)

    @property
    def is_fleet(self):
        return self.unit_type == UnitType.Fleet


class Army(Unit):

    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)
        self.unit_type = UnitType.Army

    def __repr__(self):
        return 'A {}'.format(self.loc.id.name)


class Fleet(Unit):
    """ Fleets are special units can be in a water tile and land tiles with coasts """
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)
        self.origin_sea = loc
        self.unit_type = UnitType.Fleet

    def __repr__(self):
        return 'F {}'.format(self.loc.id.name)

    def reachable_tiles(self, convoy_=False) -> Set[Province]:
        """ fleets can reach every tile that are adjacent """

        if not convoy_:
            return self.loc.neighbours

        return super().reachable_tiles(convoy_=True)


def make_unit(type: UnitType, loc: Province, owner: Player, board: 'Board') -> Unit:
    """ Unit Factory """

    if type == UnitType.Fleet:
        return Fleet(loc, owner, board)

    return Army(loc, owner, board)


if __name__ == '__main__':
    from dgame.board import Board
    import sys
    sys.stderr = sys.stdout

    players = [Player(), Player()]
    board = Board(Diplomacy1901(), players)

    print('=' * 75)
    for i in range(1, 76):

        tile = board.get_tile_by_id(i)

        unittype = UnitType.Army
        if tile.is_water:
            unittype = UnitType.Fleet

        unit = board.add_unit(unittype, tile, players[0])

        print(i, unit, unit.reachable_tiles(), ' == ', board.get_tile_by_id(i).neighbours)

        board.disband(unit)

        assert len(players[0].units) == 0
        assert len(board.loc_unit) == 0
        assert len(board.units) == 0

    # -------------------------------------------------------------------------------






    print('=' * 80)
    a1 = board.add_unit(UnitType.Army, board.get_tile_by_name('NOR'), players[0])
    print(a1, a1.reachable_tiles())
    f1 = board.add_unit(UnitType.Fleet, board.get_tile_by_name('NTH'), players[0])
    print(a1, a1.reachable_tiles())

    print('-' * 10)
    print(a1.get_possible_order())

    from diplomacy.engine.game import Game

    game = Game()
    #game.clear_units()
    #game.set_units('TURKEY', ['A NOR', 'F NTH'])

    orders = []

    for key, value in game.get_all_possible_orders().items():
        orders.extend(value)

    for i in range(0, len(orders) // 3):

        print('{:4d} {:>30} {:>30} {:>30}'.format(i, orders[i * 3], orders[i * 3 + 1], orders[i * 3 + 2]))

    board.disband(a1)
    board.disband(f1)

    assert len(players[0].units) == 0
    assert len(board.loc_unit) == 0
    assert len(board.units) == 0

    board.add_unit(UnitType.Fleet, board.get_tile_by_name('NOR'), players[0])




