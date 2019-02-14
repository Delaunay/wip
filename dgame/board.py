from dgame.power import Player
from dgame.province import Province

from dgame.unit import Unit, make_unit
from dgame.definition import AbstractBoardDefinition

from dgame.order import Order
from dgame.order import HOLD, MOVE, CONVOY, CONVOY_MOVE, SUPPORT_MOVE, SUPPORT, RETREAT, BUILD, DISBAND, WAIVE

from typing import List, Optional


class Board:
    """
        This represent a board instance with all the current unit placement.
        This is an acceleration data structure that holds all the information to do order computation quickly.
        It does not do any checks. Its job is to process orders and compute the next board state.
        All orders should go through this.
    """

    def __init__(self, board_definition: AbstractBoardDefinition, players: List[Player]):
        self._definition = board_definition
        self._players = players
        self._units = set()
        self._loc_unit = {}

        self.instruction_dispatch = {
            HOLD: self.hold,
            MOVE: self.move_unit,
            CONVOY: self.convoy,
            CONVOY_MOVE: self.convoy_move,
            SUPPORT: self.support,
            SUPPORT_MOVE: self.support_move,
            RETREAT: self.retreat_unit,
            BUILD: self.build_unit,
            DISBAND: self.disband_unit,
            WAIVE: self.waive
        }

    @staticmethod
    def __check_ownerships(player: Player, unit: Unit, message: str):
        assert unit.owner is player, '{}; the unit {} is owned by {} not {}'.format(message, unit, unit.owner, player)

    def process_order(self, player: Player, order: Order):
        return self.instruction_dispatch[order.order](player, order)

    def build_unit(self, player: Player, order: Order) -> Unit:
        """ Create a new unit of type `type`('A' or 'F') for `player` in `loc` """
        unit = make_unit(order.unit.unit_type, order.unit.loc, player, self)
        unit.owner = player
        player.units.add(unit)
        self._units.add(unit)
        self._loc_unit[self.get_tile_by_id(unit.loc.without_coast)] = unit
        return unit

    # can throw if unit does not belong to player
    def disband_unit(self, player: Player, order: Order):
        # Get current unit
        unit = self._loc_unit.pop(order.unit.loc)

        self.__check_ownerships(player, unit, 'Cannot disband')

        player.units.remove(unit)
        self._units.discard(unit)

    def move_unit(self, player: Player, order: Order):
        unit = self._loc_unit.pop(order.unit.loc)

        self.__check_ownerships(player, unit, 'Cannot move')

        self._loc_unit[self.get_tile_by_id(order.dest.without_coast)] = unit
        unit.loc = order.unit.dest

    def hold(self, player: Player, order: Order):
        pass

    def convoy(self, player: Player, order: Order):
        pass

    def convoy_move(self, player: Player, order: Order):
        self.move_unit(player, order)

    def support(self, player: Player, order: Order):
        pass

    def support_move(self, player: Player, order: Order):
        pass

    def retreat_unit(self, player: Player, order: Order):
        self.move_unit(player, order)

    def waive(self, player: Player, order: Order):
        pass

    # Game State Query
    def get_unit_at(self, loc: Province) -> Optional[Unit]:
        return self._loc_unit.get(self.get_tile_by_id(loc.without_coast))

    def get_tile_by_id(self, index: int) -> Province:
        return self._definition.PROVINCE_DB[index]

    def get_tile_by_name(self, name: str) -> Province:
        return self._definition.province_from_string(name)

    def units(self):
        return self._units

    def players(self):
        return self._players
