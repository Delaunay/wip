

from diplomacy import Game
g = Game()
#g.clear_units()

g.set_units('ENGLAND', ['A YOR', 'F NTH'])


for i in g.get_all_possible_orders('YOR'):
    print(i)


#['A LVP H', 'A LVP - WAL', 'A LVP - CLY', 'A LVP - YOR', 'A LVP - EDI', 'A LVP S F NTH - YOR', 'A LVP S F NTH - EDI']

# print('A LVP S F NTH - YOR' in g.get_all_possible_orders())

#True


