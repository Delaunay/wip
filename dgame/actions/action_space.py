

def reachable_province_army(self, convoy_: bool, path, reachable):
    """ """


def reachable_province_fleet(self, convoy_: bool, path, reachable):
    """ fleets can reach every tile that are adjacent """

    if not convoy_:
        for tile in self.loc.neighbours:
            # for a tile to be reachable by a fleet it needs to be either water
            # or a land tile with a common sea between current loc and dest loc
            has_common_sea = self.loc in tile.seas or len(self.loc.seas.intersection(tile.seas)) > 0

            if (tile.is_water or has_common_sea) and tile not in path:
                if tile not in reachable:
                    reachable[tile] = set()

                reachable[tile].add(path)

        return reachable

    reachable_province_army(self, convoy_=True, path=cons(self.loc, path), reachable=reachable)


def reachable_province(self, unit):
    """ return a set of tuples representing a reachable province and the path taken to get there for a given unit"""



def possible_move_order(self, unit):
    """ return a set of all possible move order that can be made by a given unit """



def get_all_possible_move_orders(board, move_orders=None):
    """ return a set of all possible move order that can be made for a specific board for all units """

    other_orders = {}
    if move_orders is None:
        move_orders = {}

    for unit in board.units():
        unit.get_possible_move_order(other_orders, move_orders)

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
                elif o1.order == CONVOY_MOVE or o2.order == CONVOY_MOVE:
                    # in a `convoy move` the move (o2.unit) can be supported
                    # but the one doing the move cannot support
                    # i.e o1 has to be

                    # F HOL S A YOR - BEL  (A YOR - BEL VIA NTH)
                    # but A YOR S F HOL - BEL is not possible
                    if o1.path is None and o2.path is not None:
                        target = o2.unit

                        # unit cannot support AND convoy
                        if unit.loc not in o2.path:
                            order = support_move(unit, target=target, dest=o2.dest)
                            corder.add(order)
                        else:  # Duplicate ?
                            order = convoy(unit, target, dest=o2.dest)
                            corder.add(order)
                            #print(order, set(map(lambda x: str(x), o2.path)))
                else:
                    target = o2.unit
                    corder.add(support_move(unit, target=target, dest=o2.dest))

                    # http://web.inter.nl.net/users/L.B.Kruijswijk/#6.B
                    # 6.B.8 SUPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE
                    if o2.dest is not dest_nc:
                        corder.add(support_move(unit, target=target, dest=dest_nc))

    return other_orders
