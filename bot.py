__author__ = 'RAEON'

from session import Session
from buffer import Buffer
from cell import Cell
import random
import time
import math

class Bot(object):

    def __init__(self, game):
        self.game = game

        # core variables
        # self.running = False  # no point, is there? we have is_connected() and is_alive()
        # self.thread = None  # instances are updated by their Game or Server if no game has been found yet
        self.session = Session()
        self.buffer = Buffer()

        # game information
        self.name = 'Test'  #''.join([random.choice('0123456789abcdefghijlkmnopqrstuvwxyz') for i in range(8)])
        self.last_x = 0  # last sent mouse X coordinate
        self.last_y = 0  # last sent mouse Y coordinate
        self.view_x = 0  # viewport x
        self.view_y = 0  # viewport y
        self.view_w = 0  # viewport width
        self.view_h = 0  # viewport height

        # our state
        self.has_sent_init = False
        self.last_sent_spawn = 0
        self.last_update = 0

        # cell information
        self.ids = []  # list of ids (to get cell, query id in all_cells)
        # no longer track cell ids
        self.ladder = []
        self.mode = 'ffa'

    def connect(self, host, port):
        if not self.is_connected() and (time.time() - self.game.last_connect > 15):
            if self.session.connect(host, port):
                print('[' + self.name + '] Connected')
                # reset game variables
                self.last_x = 0
                self.last_y = 0
                self.view_x = 0
                self.view_y = 0
                self.view_w = 0
                self.view_h = 0

                # reset some more variables
                self.game.last_connect = time.time()
                self.has_sent_init = False
                self.last_sent_spawn = 0

                # clear our lists
                self.ids = []
                self.ladder = {}

                # try and become ALIIIIVE!
                self.send_init()
                self.send_spawn()
                self.send_move_relative(0, 0)  # cuz fuck moving, thats why

                self.n_updates = 0
                return True
            print('[' + self.name + '] Failed to connect')
        return False
    
    # version 520
    def disconnect(self):
        if self.is_connected():
            # disconnect
            self.session.disconnect()
            
            # remove ourselves from all cell watchers
            # in game cell objects
            for cell in self.game.cells.values():
                cell.remove_watcher(self)
            
            # remove all bot.ids from game.ids
            for id in self.ids:
                self.game.remove_id(id)
                if self.has_id(id):
                    self.remove_id(id)
                    self.game.remove_id(id)
            # game deletes all cells w/o watchers
            return True
        return False
    
    # version 520
    def update(self):
        # connect if not connected
        if not self.is_connected():
            self.connect(self.game.host, self.game.port)
            return False

        # spawn if not alive
        if not self.is_alive():
            self.send_spawn()
            # dont return: if we do, we dont parse spawn packet

        # get all data
        all = []
        all.extend(self.session.inbound)
        self.session.inbound = self.session.inbound[len(all):]

        if (len(all) != 0):
          self.n_updates += 1

        # parse all data
        for data in all:
            self.buffer.fill(data)
            packet = self.buffer.read_byte()
            self.parse_packet(packet)
        
        if not self.last_update == self.game.timestamp:
            # if we didn't receive an update this tick, we dont need to check for destroys.
            return

        # removing dead cells no longer happens in bot.py
        # cells are only removed on a packet, or when there are no watchers (only on disconnect)
        return True

    def act(self):
        # todo: write AI
        pass

    def parse_packet(self, id):
        b = self.buffer
        if id == 16:
            self.last_update = self.game.timestamp
            self.parse_mergers()
            self.parse_updates()
            self.parse_deaths()
        elif id == 17:
            x = b.read_float()
            y = b.read_float()
            ratio = b.read_float()
            print('[17]', x, y, ratio)
        elif id == 20:
            for id in self.ids:
                self.game.remove_id(id)
            self.ids = []
            
            print('[20] cell reset')
        elif id == 32:
            id = b.read_int()
            self.add_id(id)
            self.game.add_id(id)
            print('[32] ', id)
        elif id == 49:
            self.ladder = {}
            self.mode = 'ffa'
            amount = b.read_int()
            for i in range(0, amount):
                id = b.read_int()
                self.ladder[id] = b.read_string()

            self.game.ladder = self.ladder.copy()
            self.game.mode = 'ffa'
            #print('[49]')
        elif id == 50:
            # the 3rd ladder version, original was 48 (non-indexed ladder), 49 (indexed) and now 50
            self.ladder = []
            count = b.read_int()
            for i in range(0, count):
                self.ladder.append(b.read_float())

            if len(self.game.ladder) == 0:
                self.game.ladder = self.ladder.copy()
                self.game.mode = 'teams'
            #print('[50]')
        elif id == 64:
            self.game.view_x = self.view_x = b.read_double()
            self.game.view_y = self.view_y = b.read_double()
            self.game.view_w = self.view_w = b.read_double()
            self.game.view_h = self.view_h = b.read_double()
            print('[64] viewport:', self.view_x, self.view_y, self.view_w, self.view_h)
    
    # version 520
    def parse_mergers(self):
        amount = self.buffer.read_short()
        for i in range(0, amount):
            hunter, prey = self.buffer.read_int(), self.buffer.read_int()
            if self.game.has_id(hunter) and self.game.has_id(prey):  # if we both know these cells
                # self.ids: our own cells ids
                # game.ids: all bot cell ids
                # game.cells: all global cell objects
                
                # game.cells: remove eaten cell from global cells
                cell = self.game.get_cell(prey)  # prey = prey_id
                self.game.remove_cell(prey)
                
                # self.ids/game.ids: remove cell id from bot and game if it is our own
                if self.has_id(cell.id):
                    self.remove_id(cell.id)
                    self.game.remove_id(cell.id)
                print('[game/parse_mergers] %d ate %d' % (hunter, prey))
    
    # version 520
    def parse_updates(self):
        b = self.buffer
        current_time = time.time()
        while True:
            id = b.read_int()

            if id == 0:
                break

            x = b.read_short()
            y = b.read_short()
            size = b.read_short()

            red = b.read_byte()
            green = b.read_byte()
            blue = b.read_byte()

            color = (red, green, blue)

            byte = b.read_byte()

            virus = (byte & 1)
            agitated = (byte & 16)  # what is this?

            # skipping bytes, no idea what the purpose is
            if (byte & 2):
                b.skip(4)
            elif (byte & 4):
                b.skip(8)
            elif (byte & 8):
                b.skip(16)

            # read name
            name = b.read_string()
            
            # if cell is not known globally:
            #   create global instance
            # if cell in self.ids:
            #   set owner to self

            # check if this cell is known globally
            if self.game.has_cell(id):
                # known globally

                # update global cell
                cell = self.game.get_cell(id)
                #print(str(current_time - cell.last_update))

                t = current_time - cell.last_update

                if (t > 0.0):

                  vx = (float(x) - float(cell.x))/t
                  vy = (float(y) - float(cell.y))/t

                  cell.vx = (vx + cell.vx)/2.0
                  cell.vy = (vy + cell.vy)/2.0

                  v = math.sqrt(cell.vx*cell.vx + cell.vy*cell.vy)
                  max_velocity = 800

                  if v > max_velocity:
                    cell.vx *= (max_velocity/v)
                    cell.vy *= (max_velocity/v)
                    cell.x = x
                    cell.y = y
                  else:
                    cell.x += cell.vx*t
                    cell.y += cell.vy*t

                  cell.interpolated_x = cell.x
                  cell.interpolated_y = cell.y
                  cell.last_update = current_time
                
                cell.size = size
                cell.color = color
                cell.virus = virus
                cell.agitated = agitated
                cell.timestamp = self.game.timestamp
            else:
                # not known globally
                
                # create new global cell
                cell = Cell(id, x, y, size, color, virus, agitated, name)
                cell.watchers.append(self)
                cell.timestamp = self.game.timestamp

                # set owner if it is ours
                if self.has_id(id):
                    cell.owner = self
                
                # add cell to global cells
                self.game.add_cell(cell)
    
    # version 520
    def parse_deaths(self):
        amount = self.buffer.read_int()
        for i in range(0, amount):
            id = self.buffer.read_int() 
            
            # if it is one of ours
            if self.has_id(id):
                self.remove_id(id)
                self.game.remove_id(id)
                if len(self.ids) == 0:
                    self.send_spawn()
                    print("[bot/parse_deaths] No cells left, respawning")
            
            # remove cell globally
            if self.game.has_cell(id):
                cell = self.game.get_cell(id)
                cell.remove_watcher(self)
                self.game.remove_cell(id)

    def send_init(self):
        if self.is_connected() and not self.has_sent_init:
            self.has_sent_init = True

            self.buffer.write_byte(254)
            self.buffer.write_int(4)
            self.buffer.flush_session(self.session)

            self.buffer.write_byte(255)
            self.buffer.write_int(1)
            self.buffer.flush_session(self.session)
            return True
        return False

    def send_spawn(self):
        if self.is_connected() and (time.time() - self.last_sent_spawn > 4):
            for cell in self.game.cells.values():
                cell.remove_watcher(self)
            self.last_sent_spawn = time.time()
            self.buffer.write_string(self.name)
            self.buffer.flush_session(self.session)
            return True
        return False

    def send_move(self, x, y):
        if self.is_connected() and self.is_alive():
            if not (self.last_x == x and self.last_y == y):
                # update our last variables
                self.last_x = x
                self.last_y = y

                # send new coordinates
                self.buffer.write_byte(16)
                self.buffer.write_double(x)
                self.buffer.write_double(y)
                self.buffer.write_int(0)

                # flush
                self.buffer.flush_session(self.session)

                return True
        return False

    def send_move_relative(self, rel_x, rel_y):
        x, y = self.get_center()
        x += rel_x
        y += rel_y
        return self.send_move(x, y)

    def send_split(self, times=1):
        if self.is_connected() and self.is_alive():
            for i in range(0, times):
                self.buffer.write_byte(17)
                self.buffer.flush_session(self.session)
            return True
        return False

    def send_throw(self, times=1):
        if self.is_connected() and self.is_alive():
            for i in range(0, times):
                self.buffer.write_byte(21)
                self.buffer.flush_session(self.session)
            return True
        return False

    def send_spectate(self):
        if self.is_connected():
            self.buffer.write_byte(1)
            self.buffer.flush_session(self.session)
            return True
        return False

    def get_center(self):
        x = 0
        y = 0
        amount = 0
        for id in self.ids:
            cell = self.game.get_cell(id)
            if cell:
                x += cell.x
                y += cell.y
                amount += 1
        amount = max(1, amount)  # prevent div by zero
        return x/amount, y/amount

    def get_interpolated_center(self, current_time):
      x = 0
      y = 0
      amount = 0
      for id in self.ids:
        cell = self.game.get_cell(id)
        if cell:
          x += cell.interpolated_x
          y += cell.interpolated_y
          amount += 1
      amount = max(1, amount)
      return x/float(amount), y/float(amount)


    def get_mass(self):
        mass = 0
        for id in self.ids:
            cell = self.game.get_cell(id)
            if cell:
                mass += cell.size
        return mass

    def is_alive(self):
        return len(self.ids) > 0

    def is_connected(self):
        return self.session.is_connected()

    def add_id(self, id):
        if not self.has_id(id):
            self.ids.append(id)
            return True
        return False

    def remove_id(self, id):
        if self.has_id(id):
            self.ids.remove(id)
            return True
        return False

    def has_id(self, id):
        return id in self.ids

