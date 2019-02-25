
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
