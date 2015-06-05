__author__ = 'RAEON'

import pygame
from pygame.locals import *
from time import time, sleep
from pygame import gfxdraw

class GameViewer(object):

    def __init__(self, game):
        self.game = game

        # initialize pygame
        pygame.init()

        # screen
        self.resolution = self.width, self.height = 800, 800
        self.screen = pygame.display.set_mode(self.resolution)

        # background (black)
        self.background = pygame.Surface(self.resolution)
        self.background.convert()
        self.background.fill((0, 0, 0))

        # font
        pygame.font.init()
        self.font_size = 16
        self.font = pygame.font.SysFont('Arial', self.font_size)

        # fps
        self.frames = 0
        self.last_frames = 0
        self.last_time = 0.0
        self.fps = 0

        # updates
        self.bot_updates = 0

        # render flags
        self.render_special = False

        self.scale = 0

        # center view on bot
        self.centered = False

        # display game data
        self.display_data = False

    def run(self):
        lastsecondtick = time()
        while True:
          if (time() - self.last_time) > 0.0:

            self.render()

            # check to see if an entire second has passed in order to
            # increment fps counter and bot updates counter
            if (time() - lastsecondtick > 1.0):
              self.fps = self.frames
              self.frames = 0
              lastsecondtick = time()

              bot = self.game.bots[0]
              self.bot_updates = bot.n_updates
              bot.n_updates = 0

            self.frames += 1
            self.last_time = time()

        pygame.quit()

    def render(self):
        if self.scale == 0:
            self.scale = self.game.view_w / 800
            if self.scale == 0:
              self.scale = 2
        
        current_time = time()

        # handle events (user input)
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            elif event.type == MOUSEMOTION:
                x, y = event.pos
                bot = self.game.bots[0]
                bot_x, bot_y = bot.get_interpolated_center(current_time)
                for bot in self.game.bots:
                    #bot.send_move_relative(5, 5)
                    if (self.centered == False):
                      bot.send_move(x*self.scale, y*self.scale)
                    else:
                      bot.send_move((x - self.width/2)*self.scale + bot_x, (y
                        - self.height/2)*self.scale + bot_y)
            elif event.type == KEYDOWN:
                if event.key == K_w:
                    for bot in self.game.bots:
                        bot.send_throw(1)
                elif event.key == K_SPACE:
                    for bot in self.game.bots:
                        bot.send_split(1)
                elif event.key == K_r:
                    for bot in self.game.bots:
                        bot.send_spawn()
                elif event.key == K_f:
                    self.render_special = True
                elif event.key == K_z:
                    self.centered = not self.centered
                elif event.key == K_d:
                    self.display_data = not self.display_data
            elif event.type == KEYUP:
                if event.key == K_f:
                    self.render_special = False

            if event.type == MOUSEBUTTONDOWN:
              if event.button == 4:
                if self.centered:
                  self.scale /= 1.1
              if event.button == 5:
                if self.centered:
                  self.scale *= 1.1
        
        
        # handle output (rendering)

        # clear screen
        self.screen.blit(self.background, (0, 0))

        # draw cells
        values = self.game.cells.copy().values()

        scale = self.scale
        #print("rendering : " + str(len(values)) + " cells")
        current_time = time()
        for cell in values:

            cell.update_interpolation(current_time)

            # draw circle
            # print('[cell]', cell.x/scale, cell.y/scale, cell.color, cell.size/scale, scale)

            # get our own smallest cells size
            smallest_size = 0
            for i in self.game.ids:
                c = self.game.get_cell(i)
                if c is not None:
                    if c.size > smallest_size:
                        smallest_size = c.size

            color = (0, 255, 0)  # green
            if smallest_size == cell.size:
                color = (255, 255, 0)  # yellow
            elif smallest_size < cell.size:
                color = (255, 0, 0)  # red

            bot = self.game.bots[0]
            x, y = bot.get_interpolated_center(current_time)
           
            # draw cell
            if (self.centered == False):
                if int(cell.size/scale) > 10:
                  pygame.gfxdraw.aacircle(self.screen, int(cell.interpolated_x/scale), int(cell.interpolated_y/scale), int(cell.size/scale), cell.color)
                pygame.gfxdraw.filled_circle(self.screen, int(cell.interpolated_x/scale), int(cell.interpolated_y/scale), int(cell.size/scale), cell.color)
            else:
                if int(cell.size/scale) > 10:
                  pygame.gfxdraw.aacircle(self.screen, int((cell.interpolated_x - x)/scale + self.width/2),
                                                             int((cell.interpolated_y - y)/scale + self.height/2),
                                                             int(cell.size/scale), cell.color)
                pygame.gfxdraw.filled_circle(self.screen, int((cell.interpolated_x - x)/scale + self.width/2),
                                                             int((cell.interpolated_y - y)/scale + self.height/2),
                                                             int(cell.size/scale), cell.color)

            # draw name
            if cell.name is not '':
                # render name above cell
                text = self.font.render(cell.name, 0, color)
                text_rect = text.get_rect()

                if (self.centered == False):
                  text_rect.centerx = int(cell.interpolated_x/scale)
                  text_rect.centery = int((cell.interpolated_y - cell.size)/scale - 5)
                else:
                  text_rect.centerx = int((cell.interpolated_x - x)/scale + self.width/2)
                  text_rect.centery = int((cell.interpolated_y - cell.size - y)/scale - 5 + self.height/2) 
                self.screen.blit(text, text_rect)

            if cell.size > 20 and not cell.virus:
                # render mass under cell
                num = str(round(cell.size))
                if self.render_special:
                    num = str(cell.id)
                text = self.font.render(num, 0, color)
                text_rect = text.get_rect()
                if (self.centered == False):
                  text_rect.centerx = int(cell.interpolated_x/scale)
                  text_rect.centery = int((cell.interpolated_y + cell.size)/scale + (self.font_size / 2))
                else:
                  text_rect.centerx = int((cell.interpolated_x - x)/scale + self.width/2)
                  text_rect.centery = int((cell.interpolated_y - y + cell.size)/scale + (self.font_size/2) + self.height/2)
                self.screen.blit(text, text_rect)

                if self.render_special:
                    text = self.font.render(str(len(cell.watchers)), 0, color)
                    text_rect = text.get_rect()
                    text_rect.centerx = int(cell.interpolated_x/scale)
                    text_rect.centery = int((cell.interpolated_y + cell.size)/scale + 3 + (self.font_size))
                    self.screen.blit(text, text_rect)

        # update fps

        #self.draw_debug()
        self.draw_leaderboard()

        #draw display data
        if (self.display_data):
          self.draw_displaydata()

        # flip buffers
        pygame.display.flip()

        return True

    def draw_debug(self):
        # update fps
        self.frames += 1
        if time() - self.timer > 1:
            self.timer = time()
            self.last_frames = self.frames
            self.frames = 0

        lines = []
        lines.append('FPS: ' + str(self.last_frames))
        lines.append('Bot/Cell_IDs: ' + str(self.game.bots[0].ids))
        lines.append('Game/Cell_IDs: ' + str(self.game.ids))
        lines.append('Server: ' + self.game.host + ':' + str(self.game.port))
        lines.append('Pos: ' + str(self.game.bots[0].get_center()))
        self.draw_lines(lines)

    def draw_lines(self, lines):
        x = 5
        y = 5
        for line in lines:
            text = self.font.render(line, 0, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.left = x
            text_rect.top = y
            y += self.font_size - 3
            self.screen.blit(text, text_rect)

    def draw_leaderboard(self):
        ladder = self.game.ladder
        x = 800 - 5
        y = self.font_size / 2
        i = 0

        if hasattr(ladder, 'values'):
          for name in ladder.values():
              i += 1
              text = self.font.render(name + ' #' + str(i), 0, (255, 255, 255))
              text_rect = text.get_rect()
              text_rect.right = x
              text_rect.top = y
              self.screen.blit(text, text_rect)
              y += self.font_size - 3

    def draw_displaydata(self):

      y = 0

      text = self.font.render("frames per second : " + str(self.fps), 0, (255, 255, 255))
      text_rect = text.get_rect()
      text_rect.left = 0
      text_rect.top = y
      self.screen.blit(text, text_rect)
      y += self.font_size

      text = self.font.render("updates per second : " + str(self.bot_updates), 0, (255, 255, 255))
      text_rect = text.get_rect()
      text_rect.left = 0
      text_rect.top = y
      self.screen.blit(text, text_rect)
      y += self.font_size

      text = self.font.render("number of bots : " + str(len(self.game.bots)), 0, (255, 255, 255))
      text_rect = text.get_rect()
      text_rect.left = 0
      text_rect.top = y
      self.screen.blit(text, text_rect)
      y += self.font_size

      text = self.font.render("number of cells : " + str(len(self.game.cells)), 0, (255, 255, 255))
      text_rect = text.get_rect()
      text_rect.left = 0
      text_rect.top = y
      self.screen.blit(text, text_rect)
      y += self.font_size
