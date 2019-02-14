from typing import Tuple
import re

from dgame.province import Province


class AbstractBoardDefinition:
    """
        This is an abstract class definition how a board is structured.
        The Game engine should be able to handle any kind of board given its definition.

        This class holds the adajency list used by the dgame engine to resolve orders
    """
    PROVINCE_DB: Tuple[any]

    def initial_condition(self):
        raise NotImplementedError

    def province_from_string(self, name: str) -> 'Provinces':
        """

            :param name:
            :return:
            :type name: str
            :rtype: Provinces
        """
        raise NotImplementedError


def make_database(powers, unowned, provinces, adjacency_list, spring, year, phase):

    data = []

    properties = {
        item[1].upper(): item for item in adjacency_list
    }

    supply_centers = set(unowned)
    home_center = set()

    # add owned supply centers
    for power in powers:
        supp = power[2]
        home_center = home_center.union(set(supp))

    supply_centers = supply_centers.union(set(home_center))

    name_to_index = {}
    shut = set()

    for index, province in enumerate(provinces):
        name = province[1][0].upper()
        name_to_index[name] = index

        if properties[name][0] == 'SHUT':
            shut.add(index)

    for index, province in enumerate(provinces):
        short = province[1][0].upper()

        adjacency = set([name_to_index[i.upper()] for i in properties[short][2]])
        seas = set(filter(lambda x: properties[x.upper()][0] == 'WATER', properties[short][2]))

        data.append(
            Province(
                pid=index,
                name=province[0],
                short=short,
                supply_center=short in supply_centers,
                water=properties[short][0] == 'WATER',
                home_center=short in home_center,
                coastal=properties[short][0] == 'COAST',
                without_coast=name_to_index[short.split('/')[0]] if '/' in short else index,
                neighbours=tuple(adjacency.difference(shut)),
                # neighbours that are seas
                seas=seas,
            )
        )

    # make immutable `array`
    return name_to_index, tuple(data)


class BoardDefinitionFile(AbstractBoardDefinition):
    def __init__(self, file_name: str):
        from dgame.parser import MapParser

        parser = MapParser()

        parser.parse(file_name)

        self.powers = parser.powers
        self.year = parser.year

        name, db = make_database(
            parser.powers,
            parser.unowned,
            parser.provinces,
            parser.adjacency_list,
            parser.spring,
            parser.year,
            parser.phase)

        self.name_to_index = name
        self.PROVINCE_DB = db

    def province_from_string(self, name: str) -> Province:
        return self.PROVINCE_DB[self.name_to_index[name]]

    def initial_condition(self):
        return self.powers


if __name__ == '__main__':
    filename = '/home/user1/diplomacy/diplomacy/maps/standard.map'

    defi = BoardDefinitionFile('/home/user1/diplomacy/diplomacy/maps/standard.map')

    for p in defi.PROVINCE_DB:
        print(repr(p))


