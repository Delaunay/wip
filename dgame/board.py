from dgame.power import Player
from dgame.province import Province

from dgame.unit import Unit, UnitType, make_unit
from dgame.definition import BoardDefinition

from typing import List, Optional


class Board:


    """
        This represent a board instance with all the current unit placement.
        This is an acceleration data structure that holds all the information to do order computation quickly
    """

    def __init__(self, board_definition: BoardDefinition, players: List[Player]):
        self.definition = board_definition
        self.players = players
        self.units = set()
        self.loc_unit = {}

    def add_unit(self, type: UnitType, loc: Province, player: Player) -> Unit:
        """ Create a new unit of type `type`('A' or 'F') for `player` in `loc` """
        unit = make_unit(type, loc, player, self)
        self.loc_unit[loc] = unit
        player.units.add(unit)
        return unit

    def disband(self, unit: Unit):
        self.loc_unit.pop(unit.loc)
        unit.disband()
        self.units.discard(unit)

    def move_unit(self, unit: Unit, dest: Province):
        self.loc_unit.pop(unit.loc)
        self.loc_unit[dest] = unit.loc
        unit.loc = dest

    def get_unit(self, loc: Province) -> Optional[Unit]:
        return self.loc_unit.get(loc)

    def get_tile_by_id(self, id) -> Province:
        return self.definition.PROVINCE_DB[id]

    def get_tile_by_name(self, name: str) -> Province:
        return self.definition.province_from_string(name)
