from dgame.power import Player
from dgame.province import Province

from dgame.board.unit import Unit, make_unit
from dgame.board.definition import AbstractBoardDefinition

from dgame.order import Order
from dgame.order import HOLD, MOVE, CONVOY, CONVOY_MOVE, SUPPORT_MOVE, SUPPORT, RETREAT, BUILD, DISBAND, WAIVE

from typing import List, Optional, Tuple, Set


class Board:
    """
        This represent a board instance with all the current unit placement.
        This is an acceleration data structure that holds all the information to do order computation quickly.
        It does not do any checks. Its job is to process orders and compute the next board state.
        All orders should go through this.
    """

    def __init__(self, board_definition: AbstractBoardDefinition, players: List[Player]):
        self._definition = board_definition
        self._powers = {
            p.power[0]: p for p in players
        }
        self._units = set()
        self._loc_unit = {}
        self._time = 0

        self._convoys = {}
        self.get_all_possible_convoy()

        # Board wide cache we do not want to put caches in a lot of different places
        # so we should put them in only one spot for invalidation
        self._cache = {}

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

    def invalidate_cache(self):
        self._cache = {}
        for unit in self._units:
            unit.invalidate_cache()

    def process_order(self, player: Player, order: Order):
        return self.instruction_dispatch[order.order](player, order)

    def build_unit(self, player: Player, order: Order) -> Unit:
        """ Create a new unit of type `type`('A' or 'F') for `player` in `loc` """

        unit = make_unit(order.unit.unit_type, order.unit.loc, player, self)
        unit.owner = player
        player.units.add(unit)
        self._units.add(unit)
        self._loc_unit[unit.loc.without_coast] = unit
        return unit

    # can throw if unit does not belong to player
    def disband_unit(self, player: Player, order: Order):
        # Get current unit
        unit = self._loc_unit.pop(order.unit.loc)

        self.__check_ownerships(player, unit, 'Cannot disband')

        player.units.remove(unit)
        self._units.discard(unit)

    def move_unit(self, player: Player, order: Order):
        assert self._loc_unit.get(order.dest.without_coast) is None, 'Cannot move unit {} {}'

        unit = self._loc_unit.pop(order.unit.loc.without_coast)

        self.__check_ownerships(player, unit, 'Cannot move')

        self._loc_unit[order.dest.without_coast] = unit
        unit.loc = order.dest

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
        return self._loc_unit.get(loc.without_coast)

    def get_tile_by_id(self, index: int) -> Province:
        return self._definition.PROVINCE_DB[index]

    def get_tile_by_name(self, name: str) -> Province:
        return self._definition.province_from_string(name)

    def units(self):
        return self._units

    def players(self):
        return self._players

    def get_player(self, name: str):
        return self._players[name]

    def get_all_possible_convoy(self):
        from dgame.board.convoys_paths import build_convoy_paths_cache

        cv = build_convoy_paths_cache(self._definition)

        def sort(lst):
            lst = list(lst)
            lst.sort()
            return lst

        def convert(paths):
            return ((start, tuple(sort(fleets)), tuple(sort(end))) for (start, fleets, end) in paths)

        aa = ((c, convert(p)) for c, p in sort(cv.items()))

        for count, paths in aa:
            for (start, fleets, ends) in paths:
                # if start not in self._convoys:
                #     self._convoys[start] = {}
                #
                # if count not in self._convoys[start]:
                #     self._convoys[start][count] = {}
                #
                # for dest in ends:
                #     self._convoys[start][count][dest] = set(fleets)

                for dest in ends:
                    self._convoys[(start.short, count, dest.short)] = tuple(fleets)
                    #print(start.short, count, dest.short)

                # print(start.__class__)

    def is_convoy_paths(self, loc:  Province, depth: int, dest: Province) -> Tuple[Set[Province], Set[Province]]:
        return self._convoys.get((loc.short, depth, dest.short))

    def get_convoy_path(self, loc:  Province, depth: int, dest: Province) -> Tuple[Set[Province], Set[Province]]:
        return self._convoys.get((loc.short, depth, dest.short))

    class _Power:
        """ wrapper for compatibility will be removed later """

        def __init__(self, p):
            self.power = p      # type: Power
            self.units = set()  # type: Set[Unit]

    def from_game_state(self, game):
        """ initialize a board given a game engine instance """
        from dgame.order import build
        assert self._convoys, 'The map was not initialized properly convoy are not available'

        self._powers = {}
        self._units = set()
        self._loc_unit = {}

        for name, obj in game.powers.items():
            power = self._Power(obj)
            self._powers[name] = power

            for unit in obj.units:
                unittype, loc = unit.split(' ')
                #self.build_unit(power, unittype, self.get_tile_by_name(loc))

                self.build_unit(power, build(make_unit(unittype, self.get_tile_by_name(loc))))

    def size(self):
        return len(self._definition.PROVINCE_DB)




if __name__ == '__main__':
    from dgame.definition import BoardDefinitionFile
    from dgame.order import build
    from diplomacy.utils.convoy_paths import build_convoy_paths_cache
    from diplomacy.engine.map import Map
    import time

    def make_new_game(state=None):
        diplo_board = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')
        players = [
            Player(p) for p in diplo_board.initial_condition()
        ]

        board = Board(diplo_board, players)

        if state is not None:
            for power, units in state['units'].items():
                p = board.get_player(power)
                for unit in units:
                    a, b = unit.split(' ')

                    board.process_order(p, build(make_unit(a, board.get_tile_by_name(b))))

        return board

    board = make_new_game()

    s = time.time()
    r = board.build_convoy_paths_cache()
    e = time.time()
    new = e - s
    print('NEW: ', e - s)

    m = Map()
    s = time.time()
    rr = build_convoy_paths_cache(m, 25)
    e = time.time()

    print('OLD: ', e - s, (e - s) / new)
    print(r == rr)

    def sort(lst):
        lst = list(lst)
        lst.sort()
        return lst

    def convert(paths):
        return ((str(start), tuple(sort(fleets)), tuple(sort(end))) for (start, fleets, end) in paths)

    a = ((c, convert(p)) for c, p in sort(r.items()))
    aa = ((c, convert(p)) for c, p in sort(rr.items()))

    if False:
        for (count, paths), (_, paths2) in zip(a, aa):
            print(count)

            for (start, fleets, end), (start2, fleets2, end2) in zip(sort(paths), sort(paths2)):
                print('    N', start, (list(map(lambda x: str(x), fleets))), (list(map(lambda x: str(x), end))))
                print('    O', start2, (list(map(lambda x: str(x), fleets2))), (list(map(lambda x: str(x), end2))))
                print()

    #branch = namedtuple()
    convoy = {}
    for count, paths in aa:

        for (start, fleets, ends) in paths:

            if start not in convoy:
                convoy[start] = {}

            if count not in convoy[start]:
                convoy[start][count] = set()

            convoy[start][count].add((fleets, ends))

    # for s, convoys in board._convoys.items():
    #     print(s)
    #
    #     for c, items in convoys.items():
    #
    #         for (dest, ends) in items.items():
    #
    #             val = str(list(map(lambda x: str(x), ends)))
    #             print('    ', c, dest, ': ', val, ' ' * (45 - len(val)))


    for i in range(0, 10):
        print(board.is_convoy_paths(board.get_tile_by_name('YOR'), 2, board.get_tile_by_name('EDI')))

