from diplomacy_research.benchmarks.game.province import Province
from diplomacy_research.benchmarks.game.power import Power
from diplomacy_research.benchmarks.game.order import Order
from diplomacy_research.benchmarks.game.diplomacy_europe_1901 import PROVINCE_DB
from typing import List


class Unit:
    def __init__(self, loc: Province, owner: Power):
        self.loc = loc
        self.owner = owner

    def get_possible_order(self):
        return self.possible_attack_order() + self.possible_support_order() + self.possible_hold_order()

    def possible_attack_order(self):
        raise NotImplementedError

    def possible_support_order(self):
        raise NotImplementedError

    def possible_hold_order(self):
        raise NotImplementedError


class Army(Unit):

    def __init__(self, loc: Province, owner: Power):
        super(Army).__init__(loc, owner)

    def convoy_orders(self) -> List[Order]:
        """ An army can convoy if a fleet is on neighbouring water tile"""
        if len(self.loc.coasts) == 0:
            return []

        raise NotImplementedError

    def possible_attack_order(self):
        """ Move an army to an adjacent `land` tile """
        raise NotImplementedError

    def possible_support_order(self):
        raise NotImplementedError

    def possible_hold_order(self):
        raise NotImplementedError


class Fleet(Unit):

    def __init__(self, loc: Province, owner: Power):
        super(Fleet).__init__(loc, owner)

    def possible_attack_order(self):
        """ Move a fleet to an adjacent `water` tile or `land` tile with a coast"""

        raise NotImplementedError

    def possible_support_order(self):
        raise NotImplementedError

    def possible_hold_order(self):
        raise NotImplementedError


if __name__ == '__main__':

    unit = Army(PROVINCE_DB[0], Power())

    print(unit.get_possible_order())
