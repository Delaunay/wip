from enum import auto, IntEnum, unique
from diplomacy_research.benchmarks.game.province import Province


@unique
class OrderTypes(IntEnum):
    Hold = 0
    AttackMove = 1
    ConvoyMove = 2
    Support = 3


class Order:
    order_type: OrderTypes = None
    src_loc: Province = None
    dest_loc: Province = None

    def __repr__(self):
        return '{} {} - {}'.format(self.order_type, self.src_loc, self.dest_loc)
