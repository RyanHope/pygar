__author__ = 'RAEON'

import argparse
import requests
import json
from game import Game
from server import Server
from viewer import GameViewer

parser = argparse.ArgumentParser(description="Agar.io client")
parser.add_argument('-i', '--ip', help="specify server ip")
parser.add_argument('-p', '--port', help="specify server port")
parser.add_argument('-l', '--location', help="automatic server location", default='EU-London')
parser.add_argument('-n', '--bots', type=int, help="number of bots", default=1)
parser.add_argument('--no-gui', dest='gui', action='store_false', help="don't load gui")
args = parser.parse_args()

if args.ip or args.port:
    if args.ip and args.port:
        ip, port = args.ip, args.port
    else:
        print("Must specify ip and port")
        exit(1)
else:
    r = requests.post('http://m.agar.io/', data='EU-London')
    print(r.text)
    ip, port = r.text.split(':')

# server = Server()


game = Game(None)
game.start(ip, port)
for i in range(args.bots):
    game.add_bot()

if args.gui:
    vi = GameViewer(game)
    vi.run()

#server.start(ip, int(port))

#erver.add_bot()
#server.add_bot()
