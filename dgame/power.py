

class Player:
    power = None
    units = set()
    tiles = []

    def __init__(self, name: str):
        self.power = name

