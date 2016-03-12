__author__ = 'RAEON'

from cell import Cell
from bot import Bot
import threading
import time

class Game(object):

    def __init__(self, server):
        self.server = server

        # core
        self.running = False  # running is only for the THREAD
        self.pause = False
        self.paused = False
        self.thread = None
        self.last_connect = 0

        # game information
        self.ladder = []
        self.mode = 'ffa'
        self.view_x = 0
        self.view_y = 0
        self.view_w = 0
        self.view_h = 0

        # misc
        self.timestamp = 0
        self.host = ''
        self.port = ''

        # cell information
        self.ids = []  # list of ids (to get cell, query id in all_cells)
        self.cells = {}  # maps id to cell

        # our bots that are in this game
        self.bots = []

    def start(self, host, port, token):
        if not self.running:
            self.running = True

            self.ladder = []
            self.timestamp = time.time()
            self.host = host
            self.port = port
            self.token = token

            self.ids = []
            self.cells = {}

            for bot in self.bots:
                bot.connect(host, port)

            self.thread = threading.Thread(name='GameThread', target=self.update)
            self.thread.start()

            return True
        return False

    def stop(self):
        if self.running:
            self.running = False

            for bot in self.bots:
                bot.disconnect()

            return True
        return False

    def is_running(self):
        return self.running

    # version 520
    def update(self):
        act = False
        last_act = 0
        while self.running:
            if self.pause:
                self.paused = True
                while self.pause:
                    pass
                self.paused = False

            self.timestamp = time.time()

            if act:
                act = False

            if (self.timestamp * 1000) - last_act > (1000 / 10):
                last_act = self.timestamp * 1000
                act = True

            for bot in self.bots:
                # print('[game] updating bot [' + bot.name + ']')
                bot.update()

            if act:
                for bot in self.bots:
                    bot.act()

            destroy = []
            for cell in self.cells.values():
                if not cell.has_watchers():
                    # cell isnt seen by any bot
                    destroy.append(cell.id)

            if len(destroy) > 0:
                print('[game/update] destroying cells: ' + str(destroy))
            for id in destroy:
                pass
                self.remove_cell(id)

    def add_bot(self):
        bot = Bot(self, self.token)
        self.bots.append(bot)
        if self.running:
            bot.connect(self.host, self.port)
        return bot

    def remove_bot(self):
        if len(self.bots) > 0:
            lowest = self.bots[0]
            for bot in self.bots:
                if bot.mass() < lowest.mass():
                    lowest = bot
            lowest.disconnect()
            self.bots.remove(lowest)
            return True
        return False

    # version 520
    def transfer(self, game):
        # transfer everyting from this self to game

        game.pause = True
        self.pause = True

        while not (game.paused and self.paused):
            pass

        for id in self.ids:
            if not game.has_id(id):
                game.add_id(id)

        for id in self.cells:
            if not game.has_cell(id):
                # they dont know about this cell, add it
                cell = self.get_cell(id)
                cell.timestamp = game.timestamp
                game.add_cell(cell)
            else:
                # they know about this cell,
                cell = self.get_cell(id)
                other_cell = game.get_cell(id)
                if cell.timestamp >= other_cell.timestamp:
                    # our version is more up-to-date, so update it
                    other_cell.x = cell.x
                    other_cell.y = cell.y
                    other_cell.size = cell.size
                    other_cell.color = cell.color
                    other_cell.virus = cell.virus
                    other_cell.name = cell.name
                # if their version is more up-to-date, do nothing

                # set cell as owner of other_cell
                if not cell.owner == None:
                    other_cell.owner = cell.owner

                # add watchers (bots)
                for bot in cell.watchers:
                    other_cell.add_watcher(bot)

        for bot in self.bots:
            if not bot in game.bots:
                bot.game = game
                game.bots.append(bot)

        # clear our own shit
        self.ids = []
        self.cells = {}
        self.bots = []
        self.ladder = {}
        self.mode = 'ffa'
        self.view_x = 0
        self.view_y = 0
        self.view_w = 0
        self.view_h = 0

        # unpause game
        self.pause = False
        game.pause = False

    # version 520
    def transfer_bot(self, bot, game):
        self.pause = True
        game.pause = True

        while not (self.paused and game.paused):
            pass

        # both games are paused
        # time to move over our stuff

        # move over all the bots owned cell ids
        for id in bot.ids:
            self.remove_id(id)
            game.add_id(id)

        # move over all cells seen by this bot
        for old in self.cells:
            if old.has_watcher(bot):
                # cell is seen by this bot
                # remove bot from watchers
                old.remove_watcher(bot)

                # check if the other game has it
                if game.has_cell(old.id):
                    # it does
                    # get cell and add watcher
                    cell = game.get_cell(old.id)
                    cell.add_wacher(bot)
                else:
                    # it doesnt
                    # create cell objects
                    cell = Cell(old.id, old.x, old.y, old.size, old.color, old.virus, old.name)
                    cell.timestamp = old.timestamp
                    cell.add_watcher(bot)

                    # add cell to game
                    game.add_cell(cell)

    def get_bot_count(self):
        return len(self.bots)

    def compare_ladders(self, ladder):
        if len(ladder) == 0:
            return 0
        if len(self.ladder) == 0:
            return 0

        if type(self.ladder[0]) == int:
            # teams type
            if type(ladder[0]) == int:
                # both ladders are int
                totaldiff = 0
                for i in range(0, 3):
                    diff = self.ladder[i] - ladder[i]
                    if diff < 0: diff *= -1
                    totaldiff += diff
                return round(1 - (totaldiff / 2), 2) * 100
        else:
            # ffa type
            if type(ladder[0]) == str:
                # both ladders are string
                matches = 0
                for a in self.ladder:
                    for b in ladder:
                        if a == b:
                            matches += 1
                return (matches / len(ladder) * 100)
        return 0

    # add cell to own_cells
    def add_id(self, id):
        if not self.has_id(id):
            self.ids.append(id)
            print('[game/add_id]', id)
            return True
        return False

    # remove cell from own_cells
    def remove_id(self, id):
        if id in self.ids:
            self.ids.remove(id)
            return True
        return False

    # check if cell in own_cells
    def has_id(self, id):
        return id in self.ids

    # add cell to all_cells
    def add_cell(self, cell):
        if not self.has_cell(cell.id):
            self.cells[cell.id] = cell
            return True
        return False

    # remove cell from all_cells
    def remove_cell(self, id):
        if self.has_cell(id):
            cell = self.get_cell(id)
            # remove all references to this cell
            for bot in cell.watchers:
                bot.remove_stamp(id)

            del self.cells[cell.id]
            return True
        return False

    # get cell from all_cells
    def get_cell(self, id):
        if id in self.cells:
            return self.cells[id]
        return None

    # check if cell in all_cells
    def has_cell(self, id):
        return id in self.cells
