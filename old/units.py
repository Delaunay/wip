
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




