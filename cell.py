__author__ = 'RAEON'

from time import time

class Cell(object):

    def __init__(self, id, x, y, size, color, virus, agitated, name):
        self.id = id
        self.x = x
        self.y = y
        self.interpolated_x = x
        self.interpolated_y = y
        self.last_update = time()
        self.vx = 0.0
        self.vy = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.size = size
        self.color = color
        self.virus = virus
        self.agitated = agitated
        self.name = name
        self.watchers = []
        self.owner = None
        self.timestamp = None

    def update_timestamp(self, timestamp):
        if self.timestamp < timestamp:
            self.timestamp = timestamp
            return True
        return False

    def update_interpolation(self, current_time):
      t = current_time - self.last_update
      self.interpolated_x = self.x + self.vx*t + 0.5*self.ax*t*t
      self.interpolated_y = self.y + self.vy*t + 0.5*self.ay*t*t

    def add_watcher(self, watcher):
        if not watcher in self.watchers:
            self.watchers.append(watcher)
            return True
        return False

    def remove_watcher(self, watcher):
        if watcher in self.watchers:
            self.watchers.remove(watcher)
            return True
        return False

    def has_watcher(self, watcher):
        return watcher in self.watchers

    def has_watchers(self):
        return len(self.watchers) > 0
