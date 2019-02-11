from enum import IntEnum, unique
from dgame.province import Province

@unique
class OrderTypes(IntEnum):
    Hold = 0
    Move = 1
    Convoy = 2
    Support = 3


class Order:
    order_type: OrderTypes = None
    unit: 'Unit' = None
    dest: Province = None

    def __init__(self,order, unit, dest=None):
        self.order_type = order
        self.unit = unit
        self.dest = dest

    def __repr__(self):
        return '{} {} - {}'.format(self.order_type, self.unit.loc, self.dest)


def hold(unit: 'Unit'):
    return Order(OrderTypes.Hold, unit)


def move(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Move, unit, dest)


def convoy(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Convoy, unit, dest)


def support(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Support, unit, dest)


