from dgame.province import Province
from dgame.power import Player
from dgame.order import Order, move, hold, support, convoy
from dgame.diplomacy_europe_1901 import Diplomacy1901

from enum import IntEnum, unique
from typing import List, Set


@unique
class UnitType(IntEnum):
    Army = 0
    Fleet = 1


class Unit:
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        self.loc = loc
        self.owner = owner
        self.board = board

    def get_possible_order(self):
        return self.possible_attack_order() + self.possible_support_order() + self.possible_hold_order()

    def possible_attack_order(self):
        raise NotImplementedError

    def possible_support_order(self):
        pass

    def possible_hold_order(self):
        return [hold(self)]

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
        return NotImplementedError


class Army(Unit):

    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)

    @property
    def is_feet(self):
        return False

    def __repr__(self):
        return 'A {}'.format(self.loc.id.name)

    def convoy_orders(self) -> List[Order]:
        """ An army can convoy if a fleet is on neighbouring water tile"""
        if len(self.loc.coasts) == 0:
            return []

        raise NotImplementedError

    def possible_attack_order(self):
        """ Move an army to an adjacent `land` tile """
        raise NotImplementedError

    def possible_support_order(self):
        raise NotImplementedError


class Fleet(Unit):
    """ Fleets are special units can be in a water tile and land tiles with coasts """
    def __init__(self, loc: Province, owner: Player, board: 'Board'):
        super().__init__(loc, owner, board)
        self.origin_sea = loc

    @property
    def is_fleet(self):
        return True

    def __repr__(self):
        return 'F {}'.format(self.loc.id.name)

    def possible_attack_order(self):
        """ Move a fleet to an adjacent `water` tile or `land` tile with a coast"""

        raise NotImplementedError

    def possible_support_order(self):
        raise NotImplementedError

    def possible_convoy_order(self):
        """ convoy order is only available for fleets, Army just use the move order """
        raise NotImplementedError

    def reachable_tiles(self, convoy_=False) -> Set[Province]:
        """ fleets can reach every tile that are adjacent"""

        if not convoy_:
            return self.loc.neighbours

        return super().reachable_tiles(convoy_=True)


def make_unit(type: UnitType, loc: Province, owner: Player, board: 'Board') -> Unit:
    if type == UnitType.Fleet:
        return Fleet(loc, owner, board)
    return Army(loc, owner, board)


if __name__ == '__main__':
    from dgame.board import Board
    import sys
    sys.stderr = sys.stdout

    players = [Player(), Player()]
    board = Board(Diplomacy1901(), players)

    print('=' * 80)
    for i in range(1, 20):

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

    board.disband(a1)
    board.disband(f1)

    assert len(players[0].units) == 0
    assert len(board.loc_unit) == 0
    assert len(board.units) == 0

    board.add_unit(UnitType.Fleet, board.get_tile_by_name('NOR'), players[0])




