from typing import List
from enum import Enum


class Province:

    def __init__(self, pid: Enum, supply_center: bool, water: bool, home_center: bool, coastal: List['Province'],
                 neighbours: List['Province']):
        self.id = pid
        self.neighbours = neighbours            # all neighbouring tiles
        self.is_supply_center = supply_center   # is a supply center
        self.is_water = water                   # is a water tile
        self.is_home_center = home_center       # is a home supply center tile
        self.coasts = coastal                   # number of neighbouring Sea Tiles

    def __repr__(self):
        return '{}(id={}, supply={}, water={}, home={}, coasts={}, {})'.format(
            self.id.name,
            self.id.value,
            self.is_supply_center,
            self.is_water,
            self.is_home_center,
            self.coasts,
            self.neighbours)

    def __str__(self):
        return self.id.name

    @property
    def name(self):
        return self.id.name



