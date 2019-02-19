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
9. WAIVE

"""

from enum import IntEnum, unique
from collections import namedtuple
from typing import TypeVar

from dgame.province import Province

# Circular reference in between modules
Unit = TypeVar('Unit')

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
    Waive = 9


HOLD = OrderTypes.Hold
MOVE = OrderTypes.Move
CONVOY = OrderTypes.Convoy
CONVOY_MOVE = OrderTypes.ConvoyMove
SUPPORT = OrderTypes.Support
SUPPORT_MOVE = OrderTypes.SupportMove
RETREAT = OrderTypes.Retreat
BUILD = OrderTypes.Build
DISBAND = OrderTypes.Disband
WAIVE = OrderTypes.Waive


class Order(namedtuple('Order', ['order', 'unit', 'dest', 'target', 'path'])):
    """
        order: order type
        unit: unit type doing the order
        src: original location of the unit
        dest: location of the unit target OR destination fo the unit doing the order
        target: unit type of the unit on dest
        target_src
    """

    def __repr__(self):
        return '<{} unit=`{}` target=`{}` dest=`{}`>'.format(self.order.name, self.unit, self.target, self.dest)

    def __str__(self):
        if self.order is HOLD:
            return '{} H'.format(self.unit)
        if self.order is SUPPORT:
            return '{} S {}'.format(self.unit, self.target)
        if self.order is SUPPORT_MOVE:
            return '{} S {} - {}'.format(self.unit, self.target, self.dest)
        if self.order is MOVE:
            return '{} - {}'.format(self.unit, self.dest)
        if self.order is CONVOY_MOVE:
            return '{} - {} VIA'.format(self.unit, self.dest)
        if self.order is CONVOY:
            return '{} C {} - {}'.format(self.unit, self.target, self.dest)
        if self.order is RETREAT:
            return '{} R {}'.format(self.unit, self.dest)
        if self.order is BUILD:
            return '{} B'.format(self.unit)
        if self.order is DISBAND:
            return '{} D'.format(self.unit)
        if self.order is WAIVE:
            return 'WAIVE'

        raise RuntimeError('Not an order')


def hold(unit: Unit) -> Order:
    return Order(order=HOLD, unit=unit, dest=None, target=None, path=None)


def move(unit: Unit, dest: Province) -> Order:
    return Order(order=MOVE, unit=unit, dest=dest, target=None, path=None)


def convoy_move(unit: Unit, dest: Province, path=None) -> Order:
    return Order(order=CONVOY_MOVE, unit=unit, dest=dest, target=None, path=path)


def convoy(unit: Unit, target: Unit, dest: Province) -> Order:
    return Order(order=CONVOY, unit=unit, dest=dest, target=target, path=None)


def support(unit: Unit, target: Unit) -> Order:
    return Order(order=SUPPORT, unit=unit, dest=None, target=target, path=None)


def support_move(unit: Unit, target: Unit, dest: Province) -> Order:
    return Order(order=SUPPORT_MOVE, unit=unit, dest=dest, target=target, path=None)


def retreat(unit: Unit, dest: Province) -> Order:
    return Order(order=RETREAT, unit=unit, dest=dest, target=None, path=None)


def disband(unit: Unit) -> Order:
    return Order(order=DISBAND, unit=unit, dest=None, target=None, path=None)


def build(unit: Unit) -> Order:
    return Order(order=BUILD, unit=unit, dest=None, target=None, path=None)


def waive() -> Order:
    return Order(order=WAIVE, unit=None, dest=None, target=None, path=None)
