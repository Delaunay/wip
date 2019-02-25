from diplomacy.engine.order import move, hold, support, support_move, convoy, convoy_move, build, disband
from diplomacy.engine.order import CONVOY_MOVE
from diplomacy.utils.linked_list import nil


class Context:

    def __init__(self):
        # [mutable] Cache of all the reachable tile per units
        self.reachable_tiles = {}

        # [immutable] Path we are currently exploring
        self.path = nil()

        # [mutable] Save all the move orders for later
        self.move_orders = {}

        # [immutable] are we inside a convoy path
        # is_convoy = False


def reachable_province(self, ctx):
    """ return a set of tuples representing a reachable province and the path taken to get there for a given unit"""
    return self.reachable_tiles(ctx)


def get_all_possible_move_orders(board, context=None):
    other_orders = [set() for _ in range(board.size())]

    if context is None:
        context = Context()

    for unit in board.units():
        unit.get_possible_move_order(other_orders, context)

    # no coast destination so we can unify fleet on coast and army supporting that fleet
    for dest_nc, orders in context.move_orders.items():

        for o1 in orders:
            unit = o1.unit
            corder = other_orders[unit.loc.without_coast.id]

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

                else:
                    target = o2.unit
                    corder.add(support_move(unit, target=target, dest=o2.dest))

                    # http://web.inter.nl.net/users/L.B.Kruijswijk/#6.B
                    # 6.B.8 SUPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE
                    if o2.dest is not dest_nc:
                        corder.add(support_move(unit, target=target, dest=dest_nc))

    return other_orders
