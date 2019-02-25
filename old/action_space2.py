

def _reachable_tiles(self, convoy, path, reachable):
    if self.is_fleet:
        return _reachable_tiles()

def _reachable_tiles_base(self, convoy, path, reachable):
    """ Compute all the reachable tiles for a given unit.
        This take into account all the adjacent land tiles and all the land tiles accessible through convoys """
    # reachable = set()

    # For each tile check if they are accessible
    for tile in self.loc.neighbours:
        if tile.is_water:
            unit = self.board.get_unit_at(tile)

            if unit is not None and unit.is_fleet and tile not in path:
                # There is a fleet on the tile so we might be able to convoy though fleet chains
                _reachable_tiles(unit, convoy_=True, path=path.append(self.loc), reachable=reachable)

        else:
            if tile not in path:
                if tile not in reachable:
                    reachable[tile] = set()

                reachable[tile].add(path)


def _reachable_tiles(self, convoy_, path, reachable):
    """ fleets can reach every tile that are adjacent """
    if not convoy_:
        for tile in self.loc.neighbours:
            # for a tile to be reachable by a fleet it needs to be either water
            # or a land tile with a common sea between current loc and dest loc
            has_common_sea = self.loc in tile.seas or len(self.loc.seas.intersection(tile.seas)) > 0

            if (tile.is_water or has_common_sea) and tile not in path:

                if tile not in reachable:
                    reachable[tile] = set()
                reachable[tile].add(path)

        return reachable

    _reachable_tiles_base(self, convoy_=True, path=path.append(self.loc), reachable=reachable)

