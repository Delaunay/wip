

from diplomacy import Game
g = Game()
#g.clear_units()

g.set_units('ENGLAND', ['A YOR', 'F NTH', 'F NWG'])


data = g.get_all_possible_orders()
for i in data:
    print(i)
    for o in data[i]:
        print('   ', o)


#['A LVP H', 'A LVP - WAL', 'A LVP - CLY', 'A LVP - YOR', 'A LVP - EDI', 'A LVP S F NTH - YOR', 'A LVP S F NTH - EDI']

# print('A LVP S F NTH - YOR' in g.get_all_possible_orders())

#True


