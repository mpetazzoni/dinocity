#!/usr/bin/env python

# DinoCity is a full-screen Super Nintendo ROM launcher designed to be
# controlled with a SNES game pad only.

__author__ = ('David Anderson <dave@natulte.net>',
              'Maxime Petazzoni <maxime.petazzoni@bulix.org>')

import clutter
import logging
import os
import struct
import sys

import rom

LOG = logging.getLogger('dinocity')

# Let's pre-compute some Clutter colors
_CLUTTER_COLOR_WHITE = clutter.color_from_string('white')
_CLUTTER_COLOR_BLACK = clutter.color_from_string('black')
_CLUTTER_COLOR_BLUE = clutter.color_from_string('blue')
_CLUTTER_COLOR_RED = clutter.color_from_string('red')

_CLUTTER_FONT_TITLE = 'Helvetica Bold 36'
_CLUTTER_FONT_GAME_TITLE = 'Helvetica Bold 24'
_CLUTTER_FONT_GAME_INFO = 'FreeMono 12'

class Game:
    """
    This class defines a game, which is represented by its associated ROM file
    and accompanying cover art.
    """

    GAME_BBOX_SIZE = (600, 436)  # Googled for chrono trigger cover art.

    def __init__(self, filename, coverart='covers/_missing.png'):
        self.filename = filename
        self.cover = self._adjust_cover_size(
                clutter.Texture(filename=coverart),
                self.GAME_BBOX_SIZE)

        self.rom = rom.SNESRom(filename)

    def _adjust_cover_size(self, texture, bbox):
        """Adjust the game cover image to the given bounding box dimensions,
        keeping the original aspect ratio."""
        (w,h) = texture.get_size()
        (wr,hr) = (w/bbox[0], h/bbox[1])

        if wr > hr:
            texture.set_size(w/wr, h/wr)
        else:
            texture.set_size(w/hr, h/hr)
            texture.set_position(w/hr/2, 0)

        return texture

    def render(self):
        self.rom.parse()

        bbox = clutter.Group()

        box = clutter.Rectangle()
        box.set_position(-2,-2)
        box.set_size(self.GAME_BBOX_SIZE[0]+4, self.GAME_BBOX_SIZE[1]+4)
        box.set_color(_CLUTTER_COLOR_BLACK)
        box.set_border_color(_CLUTTER_COLOR_RED)
        box.set_border_width(2)
        bbox.add(box)

        name = clutter.Text()
        name.set_text(self.rom.title)
        name.set_position(0, self.GAME_BBOX_SIZE[1] + 15)
        name.set_color(_CLUTTER_COLOR_WHITE)
        name.set_font_name(_CLUTTER_FONT_GAME_TITLE)
        bbox.add(name)

        info = clutter.Text()
        info.set_text('%s (%s)' % (self.filename, self.rom.get_info_string()))
        info.set_position(0, self.GAME_BBOX_SIZE[1] + 50)
        info.set_color(_CLUTTER_COLOR_WHITE)
        info.set_font_name(_CLUTTER_FONT_GAME_INFO)
        bbox.add(info)

        bbox.add(self.cover)
        return bbox


class DinoCity:

    def __init__(self, screen_size, rom_directory, cover_directory):
        self.stage = self._create_stage(screen_size)
        self.rom_directory = rom_directory
        self.cover_directory = cover_directory

    def _create_stage(self, screen_size):
        stage = clutter.Stage()
        stage.set_size(*screen_size)
        stage.connect('destroy', clutter.main_quit)
        stage.set_color(_CLUTTER_COLOR_BLACK)
        stage.connect('key-press-event', self._on_key_event)

        logo = clutter.Texture(filename='reptar.png')
        logo.set_size(64, 64)
        logo.set_position(20, 20)
        stage.add(logo)

        title = clutter.Text()
        title.set_text('DinoCity ROM launcher')
        title.set_position(100, 30)
        title.set_color(_CLUTTER_COLOR_WHITE)
        title.set_font_name(_CLUTTER_FONT_TITLE)
        stage.add(title)

        LOG.debug('Created main Clutter stage for DinoCity.')
        return stage

    def _on_key_event(self, stage, event):
        if event.keyval == clutter.keysyms.Escape:
            clutter.main_quit()

    def go(self):
        # Testing
        LOG.info('Loading game roms/simcity.smc...')
        game = Game('roms/simcity.smc', 'covers/simcity.jpg')
        bbox = game.render()
        bbox.set_position((self.stage.get_size()[0] -
                           Game.GAME_BBOX_SIZE[0]) / 2,
                          (self.stage.get_size()[1] -
                           Game.GAME_BBOX_SIZE[1]) / 2)
        self.stage.add(bbox)

#        self.stage.set_fullscreen(True)
        self.stage.show_all()
        clutter.main()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    d = DinoCity((1280, 720), 'roms/', 'covers/')
    d.go()
