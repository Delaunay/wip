from dgame.power import Player
from dgame.province import Province

from dgame.unit import Unit, make_unit
from dgame.definition import AbstractBoardDefinition

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
        self._players = {
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

    def _get_convoy_paths(self, start_location, max_convoy_length, queue):
        """ Returns a list of possible convoy destinations with the required units to get there
            Does a breadth first search from the starting location

            :param map_object: The instantiated map
            :param start_location: The start location of the unit (e.g. 'LON')
            :param max_convoy_length: The maximum convoy length permitted
            :param queue: Multiprocessing queue to display the progress bar
            :return: A list of ({req. fleets}, {reachable destinations})
            :type map_object: diplomacy.Map
        """
        from queue import Queue

        to_check = Queue()  # Items in queue have format ({fleets location}, last fleet location)
        dest_paths = {}  # Dict with dest as key and a list of all paths from start_location to dest as value

        # We need to start on a coast / port
        sloc = start_location
        if len(sloc.seas) == 0 or sloc.is_water:
            return []

        # Queuing all adjacent water locations from start
        for tile in sloc.seas:
            to_check.put(({tile}, tile))

        # Checking all subsequent adjacencies until no more adjacencies are possible
        while not to_check.empty():
            fleets_loc, last_loc = to_check.get()

            # Checking adjacencies
            for loc in last_loc.neighbours:  # type: Province

                # If we find adjacent coasts, we mark them as a possible result
                # if map_object.area_type(loc) in ('COAST', 'PORT') and '/' not in loc and loc != start_location:
                if not loc.is_water and loc.without_coast is not sloc:
                    dest_paths.setdefault(loc.without_coast, [])

                    # If we already have a working path that is a subset of the current fleets, we can skip
                    # Otherwise, we add the new path as a valid path to dest
                    for path in dest_paths[loc.without_coast]:
                        if path.issubset(fleets_loc):
                            break
                    else:
                        dest_paths[loc.without_coast] += [fleets_loc]

                # If we find adjacent water/port, we add them to the queue
                elif loc.is_water and loc not in fleets_loc and len(fleets_loc) < max_convoy_length:
                    to_check.put((fleets_loc | {loc}, loc ))

        # Merging destinations with similar paths
        similar_paths = {}
        for dest, paths in dest_paths.items():
            for path in paths:
                tuple_path = tuple(sorted(path))
                similar_paths.setdefault(tuple_path, set([]))
                similar_paths[tuple_path] |= {dest.without_coast}

        # Converting to list
        results = []
        for fleets, dests in similar_paths.items():
            results += [(start_location, set(fleets), dests)]

        # Returning
        queue.put(1)
        return results

    def display_progress_bar(self, queue, max_loop_iters):
        """ Displays a progress bar
            :param queue: Multiprocessing queue to display the progress bar
            :param max_loop_iters: The expected maximum number of iterations
        """
        import tqdm

        progress_bar = tqdm.tqdm(total=max_loop_iters)
        for _ in iter(queue.get, None):
            progress_bar.update()
        progress_bar.close()

    def build_convoy_paths_cache(self, max_convoy_length=25):
        """ Builds the convoy paths cache for a map
            :param map_object: The instantiated map object
            :param max_convoy_length: The maximum convoy length permitted
            :return: A dictionary where the key is the number of fleets in the path and
                     the value is a list of convoy paths (start loc, {fleets}, {dest}) of that length for the map
            :type map_object: diplomacy.Map
        """
        print('Generating convoy paths for {}'.format('-'))
        import multiprocessing
        import threading
        import collections

        coasts = []
        for loc in self._definition.PROVINCE_DB:
            if (not loc.is_water and len(loc.seas) > 0) and '/' not in loc.short:
                coasts.append(loc)

        # Starts the progress bar loop
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        progress_bar = threading.Thread(target=self.display_progress_bar, args=(queue, len(coasts)))
        progress_bar.start()

        # Getting all paths for each coasts in parallel
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        tasks = [(coast, max_convoy_length, queue) for coast in coasts]
        results = pool.starmap(self._get_convoy_paths, tasks)
        pool.close()
        results = [item for sublist in results for item in sublist]
        queue.put(None)
        progress_bar.join()

        # Splitting into buckets
        buckets = collections.OrderedDict({i: [] for i in range(1, len(self._definition.PROVINCE_DB) + 1)})
        for start, fleets, dests in results:
            buckets[len(fleets)] += [(start, fleets, dests)]

        # Returning
        print('Found {} convoy paths for {}\n'.format(len(results), ''))
        return buckets

    def get_all_possible_convoy(self):
        cv = self.build_convoy_paths_cache()

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

