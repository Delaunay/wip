"""

0. A LON H                     Hold Position
1. F IRI - MAO                 Attack/Attack         MAO
2. A IRI - MAO VIA             Attack/Attack         MAO using convoy
3. F NWG C A NWY - EDI         Convoy Attack/Move

4. A WAL S F LON               Support Hold
5. A WAL S F MAO - IRI         Support Attack/Attack

6. A IRO R MAO                 Retreat
7. A IRO D                     Disband
8. A LON B                     Build

"""

from enum import IntEnum, unique
from dgame.province import Province


@unique
class OrderTypes(IntEnum):
    Hold = 0
    Move = 1
    ConvoyMove = 2
    Convoy = 3
    Support = 4
    SupportMove = 5
    Retreat = 6
    Disband = 7
    Build = 8


HOLD = OrderTypes.Hold
MOVE = OrderTypes.Move
CONVOY = OrderTypes.Convoy
CONVOY_MOVE = OrderTypes.ConvoyMove
SUPPORT = OrderTypes.Support
SUPPORT_MOVE = OrderTypes.SupportMove
RETREAT = OrderTypes.Retreat
BUILD = OrderTypes.Build
DISBAND = OrderTypes.Disband


class Order:
    order_type: OrderTypes = None
    unit: 'Unit' = None
    dest: Province = None

    def __init__(self,order, unit, dest=None):
        self.order_type = order
        self.unit = unit
        self.dest = dest

    def __repr__(self):
        if self.order_type == HOLD:
            return '\'{} {} H\''.format(self.unit.unit_type, self.unit.loc.name)
        if self.order_type == SUPPORT:
            return '\'{} {} S {}\''.format(self.unit.unit_type, self.unit.loc.name, self.dest.name)
        if self.order_type == MOVE:
            return '\'{} {} - {}\''.format(self.unit.unit_type, self.unit.loc.name, self.dest.name)
        if self.order_type == CONVOY_MOVE:
            return '\'{} {} - {} VIA\''.format(self.unit.unit_type, self.unit.loc.name, self.dest.name)
        if self.order_type == CONVOY:
            return '\'{} {} C {}\''.format(self.unit.unit_type, self.unit.loc.name)
        if self.order_type == RETREAT:
            return '\'{} {} R {}\''.format(self.unit.unit_type, self.unit.loc.name, self.dest.name)
        if self.order_type == BUILD:
            return '\'{} {} B\''.format(self.unit.unit_type, self.unit.loc.name)
        if self.order_type == DISBAND:
            return '\'{} {} D\''.format(self.unit.unit_type, self.unit.loc.name)


def hold(unit: 'Unit'):
    return Order(OrderTypes.Hold, unit)


def move(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Move, unit, dest)


def convoy(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Convoy, unit, dest)


def support(unit: 'Unit', dest: Province):
    return Order(OrderTypes.Support, unit, dest)


