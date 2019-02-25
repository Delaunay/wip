import re


def clean(lst):
    no_space = map(lambda x: x.strip(), lst)
    no_empty = filter(lambda x: len(x) > 0, no_space)
    return list(no_empty)


# @dataclass
class MapDefinition:
    def __init__(self):
        self.powers = []  # type: List[Tuple[name, people, supply_centers, armies]]
        self.unowned = []
        self.provinces = []
        self.adjacency_list = []
        self.spring = None
        self.year = None
        self.phase = None


class MapParser:
    """
        Parse the file as is, the raw data will be then consumed by a board definition as initialization
    """
    def __init__(self):
        self.power = r'([A-Z]*)\s*\(([A-Z]*)\)\s*((\s[A-Z]{3}){3,})'
        self.army = r'^(A|F)\s([A-Z]{3}(/[A-Z]{2})?)'
        self.province = r'([a-zA-Z() ]*)\s*=\s([.+\-()a-z/ ]*)'
        self.properties = r'([A-Z]*)\s*([a-zA-Z]{3}(/[A-Z]{2})?)\s*ABUTS([a-zA-Z/ ]*)'
        self.index = -1
        self.line = None
        self.file = None
        self.lines = None

        self.map = MapDefinition()

    def match(self, regex):
        """ match regex with current line and return the result """
        if self.line is not None:
            return re.search(regex, self.line)

    def is_done(self):
        """ check if we have reached the end of the file """
        return self.index >= len(self.lines) - 1

    def readline(self):
        """ move the cursor one line and return it. Returns None if at the end of the file """
        if self.index >= len(self.lines) - 1:
            return None

        self.index += 1
        return self.lines[self.index]

    def next(self):
        """ get the next non empty line that is not a comment """
        self.line = self.readline()

        while self.line is not None and (len(self.line.strip()) == 0 or self.line[0] == '#'):
            self.line = self.readline()

        return self.line

    def parse_powers(self):
        """ parse a power definition Name, people name, supply centers, armies"""
        # Find the power section
        while True:
            p = self.match(self.power)

            if p is None:
                break

            self.parse_power(p)

    def parse_power(self, p):
        """ parse a power definition Name, people name, supply centers, armies"""

        name = p.group(1)
        people = p.group(2)
        supply_centers = clean(p.group(3).split(' '))
        armies = []

        # read the Armies location
        self.next()

        while True:
            a = self.match(self.army)

            if a is None:
                break

            army_type = a.group(1)
            loc = a.group(2)

            armies.append((army_type, loc))
            self.next()

        self.map.powers.append((name, people, supply_centers, armies))

    def parse_unowned(self):
        """ parse unowned supply centers """
        if self.line.startswith('UNOWNED'):
            values = clean(self.line.split(' '))[1:]
            self.map.unowned.extend(values)
            self.next()

    def parse_province_names(self):
        """ parse the list of provinces with the mapping  full_name => short
            we only allow the use of the first short name in our game
        """

        p = self.match(self.province)

        while p is not None:
            full_name = p.group(1).strip()
            shorts = clean(p.group(2).split(' '))

            self.map.provinces.append((full_name, shorts))

            self.next()
            p = self.match(self.province)

    def parse_adjacency_list(self):
        """ parse the adjacency list of each province"""
        p = self.match(self.properties)

        while p is not None:

            tile_type = p.group(1)
            name = p.group(2)
            adjacent_tiles = clean(p.group(4).split(' '))

            self.map.adjacency_list.append((tile_type, name, adjacent_tiles))

            self.next()
            p = self.match(self.properties)

    def parse(self, file_name: str):
        """ parse the definition file until the end of the file"""
        with open(file_name, 'r') as text:
            self.file = text
            self.lines = self.file.readlines()
            self.file.close()

            self.next()

            _, self.map.spring, self.map.year, self.map.phase = self.line.split(' ')

            self.next()

            while not self.is_done():

                self.parse_powers()

                self.parse_unowned()

                self.parse_province_names()

                self.parse_adjacency_list()

        return self.map


def parse_map_definition(file_name):
    """ parse a diplomacy map definition file and return the data stored inside it """
    return MapParser().parse(file_name)
