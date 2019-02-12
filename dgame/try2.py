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


class Unit:
    """  A unit is a type, location tuple """

    def __init__(self, type: chr, loc: str, owner: str = None):
        self.type = type
        self.loc = loc
        self.owner = owner
    
    def __repr__(self):
        return '{} {}'.format(self.type, self.loc)


class Order(namedtuple('Order', ['order', 'unit', 'dest', 'target'])):
    """
        order: order type
        unit: unit type doing the order
        src: original location of the unit
        dest: location of the unit target OR destination fo the unit doing the order
        target: unit type of the unit on dest
        target_src
    """

    def __repr__(self):
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
    return Order(order=HOLD, unit=unit, dest=None, target=None)


def move(unit: Unit, dest: str) -> Order:
    return Order(order=MOVE, unit=unit, dest=dest, target=None)


def convoy_move(unit: Unit, dest: str) -> Order:
    return Order(order=CONVOY_MOVE, unit=unit, dest=dest, target=None)


def convoy(unit: Unit, target: Unit, dest: str) -> Order:
    return Order(order=CONVOY_MOVE, unit=unit, dest=dest, target=target)


def support(unit: Unit, target: Unit) -> Order:
    return Order(order=SUPPORT, unit=unit, dest=None, target=target)


def support_move(unit: Unit, target: Unit, dest: str) -> Order:
    return Order(order=SUPPORT_MOVE, unit=unit, dest=dest, target=target)


def retreat(unit: Unit, dest: str) -> Order:
    return Order(order=RETREAT, unit=unit, dest=dest, target=None)


def disband(unit: Unit) -> Order:
    return Order(order=DISBAND, unit=unit, dest=None, target=None)


def build(unit: Unit) -> Order:
    return Order(order=BUILD, unit=unit, dest=None, target=None)


def waive() -> Order:
    return Order(order=WAIVE, unit=None, dest=None, target=None)


def remove_duplicates(list_with_dup):
    """ Shorthand functions to remove duplicates """
    return list(set(list_with_dup))


def get_unit_owner(game, unit: Unit) -> str:
    if not isinstance(unit, Unit):
        return game._unit_owner(unit)

    if unit.owner is None:
        # _unit_owner('A {}'.format(src)):
        unit.owner = game._unit_owner(repr(unit))
        
    return unit.owner


def get_all_possible_orders(self):
    """  :return: a list of possible orders for all locations if no locations are provided. """
    all_possible_orders = {}

    for map_loc in self.map.locs:
        map_loc = map_loc.upper()
        all_possible_orders[map_loc] = get_all_possible_orders_at(self, map_loc)

    return all_possible_orders


def get_all_possible_orders_at(self, loc):
    """ Computes a list of all possible orders for a unit in a given location
            :param loc: The location where to get a list of orders (must include coasts)
                    If not provided, returns a list of all possible orders for all locations
            :return: A list of orders for the unit, if there is a unit at location, or a list of possible
                    orders for all locations if no locations are provided.
        """

    # Otherwise finding the possible orders at that specific location
    possible_orders = []
    is_dislodged = False
    unit = None
    unit_power = None

    # If there are coasts possible, recursively adding the coasts first, then adding the loc orders
    if '/' not in loc:
        for loc_with_coast in [coast for coast in self.map.find_coasts(loc) if '/' in coast]:
            possible_orders += get_all_possible_orders_at(self, loc_with_coast)

    # Determining if there is a unit at loc
    # Dislodged unit have precedence over regular unit in Retreat phase
    for power in self.powers.values():
        dislodged = [u for u in power.retreats if u[2:] == loc.upper()]
        regular = [u for u in power.units if u[2:] == loc.upper()]
        if dislodged:
            is_dislodged = True
            unit = dislodged[0]
            unit_power = power
            break
        elif regular and not is_dislodged:
            unit = regular[0]
            unit_power = power
            if self.phase_type != 'R':
                break

    # No unit found, checking if location is a home
    if unit is None:
        if self.phase_type != 'A':
            return remove_duplicates(possible_orders)
        for power in self.powers.values():
            if loc[:3] in power.homes and 'BUILD_ANY' not in self.rules:
                unit_power = power
                break
            if loc[:3] in power.centers and 'BUILD_ANY' in self.rules:
                unit_power = power
                break

    # Not a home, and no units
    if not unit_power:
        return remove_duplicates(possible_orders)

    # Determining if we can build or need to remove units
    build_count = 0 if self.phase_type != 'A' else len(unit_power.centers) - len(unit_power.units)

    # Determining unit type and unit location
    unit_type = unit[0] if unit else ''
    unit_loc = unit[2:] if unit else ''

    unit = Unit(type=unit_type, loc=unit_loc)

    # Movement phase
    if self.phase_type == 'M':
        # Computing coasts for dest
        dest_1_hops = [l.upper() for l in self.map.abut_list(unit_loc, incl_no_coast=True)]
        dest_with_coasts = [self.map.find_coasts(dest) for dest in dest_1_hops]
        dest_with_coasts = {val for sublist in dest_with_coasts for val in sublist}

        # Hold
        # '{} H'.format(unit)
        possible_orders += [hold(unit)]

        # Move (Regular) and Support (Hold)
        for dest in dest_with_coasts:

            if self._abuts(unit_type, unit_loc, '-', dest):
                # '{} - {}'.format(unit, dest)
                possible_orders += [move(unit, dest)]

            if self._abuts(unit_type, unit_loc, 'S', dest):
                if get_unit_owner(self, 'A {}'.format(dest)):
                    # '{} S A {}'.format(unit, dest)
                    possible_orders += [support(unit, Unit('A', dest))]

                elif get_unit_owner(self, 'F {}'.format(dest)):
                    # '{} S F {}'.format(unit, dest)
                    possible_orders += [support(unit, Unit('F', dest))]

        # Move Via Convoy
        for dest in self._get_convoy_destinations(unit_type, unit_loc):
            # '{} - {} VIA'.format(unit, dest)
            possible_orders += [convoy_move(unit, dest)]

        # Support (Move)
        for dest in dest_with_coasts:

            # Computing src of move (both from adjacent provinces and possible convoys)
            # We can't support a unit that needs us to convoy it to its destination
            abut_srcs = self.map.abut_list(dest, incl_no_coast=True)
            convoy_srcs = self._get_convoy_destinations('A', dest, exclude_convoy_locs=[unit_loc])

            # Computing coasts for source
            src_with_coasts = [self.map.find_coasts(src) for src in abut_srcs + convoy_srcs]
            src_with_coasts = {val for sublist in src_with_coasts for val in sublist}

            for src in src_with_coasts:

                # Checking if there is a unit on the src location
                if get_unit_owner(self, 'A {}'.format(src)):
                    src_unit_type = 'A'
                elif get_unit_owner(self, 'F {}'.format(src)):
                    src_unit_type = 'F'
                else:
                    continue

                # Checking if src unit can move to dest (through adj or convoy), and that we can support it
                # Only armies can move through convoy
                if src[:3] != unit_loc[:3] \
                        and self._abuts(unit_type, unit_loc, 'S', dest) \
                        and ((src in convoy_srcs and src_unit_type == 'A')
                             or self._abuts(src_unit_type, src, '-', dest)):

                    # Adding with coast
                    # '{} S {} {} - {}'.format(unit, src_unit_type, src, dest)
                    possible_orders += [support_move(unit, Unit(src_unit_type, src), dest)]

                    # Adding without coasts
                    if '/' in dest:
                        # '{} S {} {} - {}'.format(unit, src_unit_type, src, dest[:3])
                        possible_orders += [support_move(unit, Unit(src_unit_type, src), dest[:3])]

        # Convoy
        if unit_type == 'F':
            convoy_srcs = self._get_convoy_destinations(unit_type, unit_loc, unit_is_convoyer=True)
            for src in convoy_srcs:

                # Checking if there is a unit on the src location
                if unit_type == 'F' and get_unit_owner(self, 'A {}'.format(src)):
                    src_unit_type = 'A'
                else:
                    continue

                # Checking where the src unit can actually go
                convoy_dests = self._get_convoy_destinations(src_unit_type, src, unit_is_convoyer=False)

                # Adding them as possible moves
                for dest in convoy_dests:
                    if self._has_convoy_path(src_unit_type, src, dest, convoying_loc=unit_loc):
                        # '{} C {} {} - {}'.format(unit, src_unit_type, src, dest)
                        possible_orders += [convoy(unit, Unit(src_unit_type, src), dest)]

    # Retreat phase
    if self.phase_type == 'R':

        # Disband
        if is_dislodged:
            # '{} D'.format(unit)
            possible_orders += [disband(unit)]

        # Retreat
        if is_dislodged:
            retreat_locs = unit_power.retreats[unit]
            for dest in retreat_locs:
                dest = dest.upper()
                if not get_unit_owner(self, 'A {}'.format(dest[:3]), coast_required=0) \
                        and not get_unit_owner(self, 'F {}'.format(dest[:3]), coast_required=0):
                    # '{} R {}'.format(unit, dest)
                    possible_orders += [retreat(unit, dest)]

    # Adjustment Phase
    if self.phase_type == 'A':
        build_sites = self._build_sites(unit_power)

        # Disband
        if build_count < 0 and unit:
            # '{} D'.format(unit)
            possible_orders += [disband(unit)]

        # Build Army / Fleet
        if build_count > 0 \
                and loc[:3] in build_sites \
                and not get_unit_owner(self, 'A ' + loc[:3], coast_required=0) \
                and not get_unit_owner(self, 'F ' + loc[:3], coast_required=0):

            if self.map.is_valid_unit('A {}'.format(loc)):
                # 'A {} B'.format(loc)
                possible_orders += [build(Unit('A', loc))]

            if self.map.is_valid_unit('F {}'.format(loc)):
                # 'F {} B'.format(loc)
                possible_orders += [build(Unit('F', loc))]

        # Waive
        if build_count > 0:
            possible_orders += [waive()]

    # Removing duplicate
    return remove_duplicates(possible_orders)


if __name__ == '__main__':
    from diplomacy.engine.game import Game
    import timeit

    game1 = Game()
    game2 = Game()

    avg_old = sum(timeit.repeat(game1.get_all_possible_orders, repeat=20, number=20)) / (10 * 10)
    avg_new = sum(timeit.repeat(lambda: get_all_possible_orders(game2), repeat=20, number=20)) / (10 * 10)

    print('avg_old {}'.format(avg_old))
    print('avg_new {}'.format(avg_new))

    print('-' * 80)
    rold = game1.get_all_possible_orders()
    rnew = get_all_possible_orders(game2)

    for key in rold:
        old = rold[key]
        new = list(map(lambda x: repr(x), rnew[key]))

        old.sort()
        new.sort()

        if set(old).difference(set(new)):
            print(key, old, new)




