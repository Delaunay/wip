import re


def clean(lst):
    no_space = map(lambda x: x.strip(), lst)
    no_empty = filter(lambda x: len(x) > 0, no_space)
    return list(no_empty)


class MapDefinition:
    powers = []
    unowned = []
    provinces = []
    adjacency_list = []
    spring = None
    year = None
    phase = None


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

        self.powers = []
        self.unowned = []
        self.provinces = []
        self.adjacency_list = []
        self.spring = None
        self.year = None
        self.phase = None

    def match(self, regex):
        if self.line is not None:
            return re.search(regex, self.line)

    def is_done(self):
        return self.index >= len(self.lines) - 1

    def readline(self):
        if self.index >= len(self.lines) - 1:
            return None

        self.index += 1
        return self.lines[self.index]

    def next(self):
        self.line = self.readline()

        while self.line is not None and (len(self.line.strip()) == 0 or self.line[0] == '#'):
            self.line = self.readline()

        return self.line

    def parse_powers(self):
        # Find the power section
        while True:
            p = self.match(self.power)

            if p is None:
                break

            self.parse_power(p)

    def parse_power(self, p):
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

        self.powers.append((name, people, supply_centers, armies))

    def parse_unowned(self):
        if self.line.startswith('UNOWNED'):
            values = clean(self.line.split(' '))[1:]
            self.unowned.extend(values)
            self.next()

    def parse_province_names(self):

        p = self.match(self.province)

        while p is not None:
            full_name = p.group(1).strip()
            shorts = clean(p.group(2).split(' '))

            self.provinces.append((full_name, shorts))

            self.next()
            p = self.match(self.province)

    def parse_adjacency_list(self):
        p = self.match(self.properties)

        while p is not None:

            tile_type = p.group(1)
            name = p.group(2)
            adjacent_tiles = clean(p.group(4).split(' '))

            self.adjacency_list.append((tile_type, name, adjacent_tiles))

            self.next()
            p = self.match(self.properties)

    def parse(self, file_name: str):
        with open(file_name, 'r') as text:
            self.file = text
            self.lines = self.file.readlines()
            self.file.close()

            self.next()

            _, self.spring, self.year, self.phase = self.line.split(' ')

            self.next()

            while not self.is_done():

                self.parse_powers()

                self.parse_unowned()

                self.parse_province_names()

                self.parse_adjacency_list()


if __name__ == '__main__':

    parser = MapParser()

    parser.parse('/home/user1/diplomacy/diplomacy/maps/standard.map')

    print(parser.unowned)
    print(parser.powers)
    #rint(parser.adjacency_list)
    #print(parser.provinces)
