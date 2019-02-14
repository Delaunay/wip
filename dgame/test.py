

from diplomacy import Game
g = Game()
#g.clear_units()
#g.set_units('ENGLAND', ['A LVP', 'F NTH'])

print(g.get_all_possible_orders('LVP'))


#['A LVP H', 'A LVP - WAL', 'A LVP - CLY', 'A LVP - YOR', 'A LVP - EDI', 'A LVP S F NTH - YOR', 'A LVP S F NTH - EDI']


print('A LVP S F NTH - YOR' in g.get_all_possible_orders())

#True


