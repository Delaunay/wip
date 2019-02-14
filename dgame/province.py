from typing import List, Optional
from enum import Enum


class Province:

    def __init__(self, pid: int, name: str, short: str, supply_center: bool, water: bool, home_center: bool, coastal: List[int],
                 without_coast: int, neighbours: List[int], seas: Optional[List[int]] = None):
        self.id = pid
        self.short = short
        self.name = name
        self.neighbours = neighbours            # all neighbouring tiles
        self.is_supply_center = supply_center   # is a supply center
        self.is_water = water                   # is a water tile
        self.is_home_center = home_center       # is a home supply center tile
        self.without_coast = without_coast      # index pointing to the tile without the coast component
        self.coasts = coastal                   # number of neighbouring Sea Tiles
        self.seas = seas

    def __repr__(self):
        return '{}(id={}, supply={}, water={}, home={}, coasts={}, -)'.format(
            self.short,
            self.id,
            self.is_supply_center,
            self.is_water,
            self.is_home_center,
            self.coasts)

    def __str__(self):
        return self.short


