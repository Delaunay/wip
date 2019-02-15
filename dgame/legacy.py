"""
    code to handle legacy code

"""

from diplomacy.engine.game import Game


class GameAdapter:

    def __init__(self, legacy_game: Game):
        self.legacy_game = legacy_game

    def __getattr__(self, item):
        return getattr(self.legacy_game, item)

    def invalidate_cache(self):
        pass


if __name__ == '__main__':
    game = GameAdapter(Game())



