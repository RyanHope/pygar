__author__ = 'RAEON'

import requests
import json
from game import Game
from server import Server
from viewer import GameViewer

# server = Server()

r = requests.post('http://m.agar.io/', data='EU-London')
print(r.text)
ip, port = r.text.split(':')

game = Game(None)
game.start(ip, port)
for i in range(0, 1):
    game.add_bot()

vi = GameViewer(game)
vi.run()

#server.start(ip, int(port))

#erver.add_bot()
#server.add_bot()
