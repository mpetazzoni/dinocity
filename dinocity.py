#!/usr/bin/env python

# DinoCity is a full-screen Super Nintendo ROM launcher designed to be
# controlled with a SNES game pad only.

__author__ = ('David Anderson <dave@natulte.net>',
              'Maxime Petazzoni <maxime.petazzoni@bulix.org>')

import clutter
import logging
import os
import struct
import subprocess
import sys
import time

import rom

LOG = logging.getLogger('dinocity')

# Specific configuration for SNES9x (at snes9x>preferences
# in ~/.snes9x/snes9x.xml):
#   <option name="full_screen_on_open" value="1"/>
#   <option name="default_esc_behavior" value="2"/>
_EMULATOR_PATH = 'snes9x-gtk'

# Let's pre-compute some Clutter colors
_CLUTTER_COLOR_WHITE = clutter.color_from_string('white')
_CLUTTER_COLOR_BLACK = clutter.color_from_string('black')
_CLUTTER_COLOR_BLUE = clutter.color_from_string('blue')
_CLUTTER_COLOR_RED = clutter.color_from_string('red')

# Define the various fonts used in the interface
_CLUTTER_FONT_TITLE = 'Helvetica Bold 36'
_CLUTTER_FONT_INFO = 'Helvetica 11'
_CLUTTER_FONT_GAME_TITLE = 'Helvetica Bold 24'
_CLUTTER_FONT_GAME_INFO = 'FreeMono 12'

class CoverArt:

    COVER_SIZE = (600, 436)  # Googled for chrono trigger cover art.

    def __init__(self, cover_directory, name):
        self.path = os.path.join(cover_directory, name)
        if not os.path.exists(self.path):
            self.path = os.path.join(cover_directory, '_missing.png')
        self.texture = clutter.Texture(filename=self.path)
        self._adjust_cover_size(self.texture, CoverArt.COVER_SIZE)

    def _adjust_cover_size(self, texture, bbox):
        """Adjust the game cover image to the given bounding box dimensions,
        keeping the original aspect ratio. The modifications are done directly
        on the given object.
        
        Args:
            texture (clutter.Texture): the Clutter texture object to resize.
            bbox (2-uple): bounding box dimensions.
        """
        (w, h) = texture.get_size()
        (wr, hr) = (w/bbox[0], h/bbox[1])

        if wr > hr:
            texture.set_size(w/wr, h/wr)
        else:
            texture.set_size(w/hr, h/hr)
            texture.set_position((bbox[0] - w/hr)/2, 0)

class Game:
    """
    This class defines a game, which is represented by its associated ROM file
    and accompanying cover art.
    """


    def __init__(self, rom_directory, cover_directory, name):
        self.name = name

        self.filename = os.path.join(rom_directory, '%s.smc' % name)
        self.coverart = CoverArt(cover_directory, '%s.jpg' % name)
        self.rom = rom.SNESRom(self.filename)
        self.rom.parse()

    def __str__(self):
        return '<Game: %s (%s)>' % (self.rom.title, self.filename)

    def render(self):
        """Render the following game in a Clutter group that can be embedded
        wherever the caller wants to."""

        g = clutter.Group()

        box = clutter.Rectangle()
        box.set_position(-2,-2)
        box.set_size(CoverArt.COVER_SIZE[0]+4, CoverArt.COVER_SIZE[1]+4)
        box.set_color(_CLUTTER_COLOR_BLACK)
        box.set_border_color(_CLUTTER_COLOR_RED)
        box.set_border_width(2)
        g.add(box)

        name = clutter.Text()
        name.set_text(self.rom.title)
        name.set_position(0, CoverArt.COVER_SIZE[1] + 15)
        name.set_color(_CLUTTER_COLOR_WHITE)
        name.set_font_name(_CLUTTER_FONT_GAME_TITLE)
        g.add(name)

        info = clutter.Text()
        info.set_text('%s (%s)' % (self.filename, self.rom.get_info_string()))
        info.set_position(0, CoverArt.COVER_SIZE[1] + 50)
        info.set_color(_CLUTTER_COLOR_WHITE)
        info.set_font_name(_CLUTTER_FONT_GAME_INFO)
        g.add(info)

        g.add(self.coverart.texture)
        return g


class DinoCity:

    def __init__(self, screen_size, rom_directory, cover_directory):
        self.rom_directory = rom_directory
        self.cover_directory = cover_directory

        # Find ROM files in the rom_directory
        self.roms = sorted(map(lambda x: x[:-4],
                           filter(lambda x: x.endswith('.smc'),
                                  os.listdir(self.rom_directory))))
        LOG.debug('Found %d ROMs in directory %s.' % (len(self.roms),
                                                     self.rom_directory))

        # Create the Clutter stage with some static interface elements
        self.stage = self._create_stage(screen_size)

        self.current_game = None
        self.current_game_id = None
        self.current_bbox = None

        if len(self.roms):
            self.current_game_id = 0
            self.display_current_game()

        LOG.info('DinoCity ready.')

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
        title.set_position(100, 15)
        title.set_color(_CLUTTER_COLOR_WHITE)
        title.set_font_name(_CLUTTER_FONT_TITLE)
        stage.add(title)

        info = clutter.Text()
        if not len(self.roms):
            info.set_text('No ROM found!')
        elif len(self.roms) == 1:
            info.set_text('1 ROM found')
        else:
            info.set_text('%d ROMs found' % len(self.roms))
        info.set_position(100, 65)
        info.set_color(_CLUTTER_COLOR_WHITE)
        info.set_font_name(_CLUTTER_FONT_INFO)
        stage.add(info)

        LOG.debug('Created main Clutter stage for DinoCity.')
        return stage

    def _on_key_event(self, stage, event):
        if event.keyval == clutter.keysyms.Escape:
            clutter.main_quit()
        elif event.keyval == clutter.keysyms.Right:
            self.next_game()
        elif event.keyval == clutter.keysyms.Left:
            self.prev_game()
        elif event.keyval == clutter.keysyms.Return:
            self.run_game()

    def run_game(self):
        """Run the currently selected game in the emulator."""
        if not len(self.roms) or self.current_game is None:
            return

        subprocess.call([_EMULATOR_PATH, self.current_game.filename])
        # TODO: add return status check if the emulator can't execute and
        # display a warning message to the user accordingly.

    def next_game(self):
        """Moves to the next game in the list. If we reached the end of the
        list, loop back to the first game."""

        if not len(self.roms):
            return

        new_current_game = self.current_game_id + 1
        if new_current_game >= len(self.roms):
            new_current_game = 0
        if new_current_game == self.current_game_id:
            return

        self.current_game_id = new_current_game
        self.display_current_game()

    def prev_game(self):
        """Moves to the previous game in the list. If we reached the beginning
        of the list, loop back to the last game."""

        if not len(self.roms):
            return

        new_current_game = self.current_game_id - 1
        if new_current_game < 0:
            new_current_game = len(self.roms) - 1
        if new_current_game == self.current_game_id:
            return

        self.current_game_id = new_current_game
        self.display_current_game()

    def display_current_game(self):
        """Show the currently selected game on screen, eventually hiding the
        game currently displayed."""

        if self.current_bbox:
            a = self.current_bbox.animate(clutter.EASE_OUT_SINE, 150,
                                          'opacity', 0)
            a.connect('completed', self._display_current_game_bh)
        else:
            self._display_current_game_bh()

    def _display_current_game_bh(self, a=None):
        if self.current_bbox:
            self.stage.remove(self.current_bbox)

        self.current_game = Game(self.rom_directory, self.cover_directory,
                                 self.roms[self.current_game_id])
        LOG.debug('Loaded %s.' % self.current_game)

        self.current_bbox = self.current_game.render()
        self.current_bbox.opacity = 0
        self._front_and_center(self.current_bbox, yoff=42)
        self.stage.add(self.current_bbox)

    def _front_and_center(self, obj, xoff=0, yoff=0):
        ssize = self.stage.get_size()
        osize = obj.get_size()
        obj.set_anchor_point(osize[0] / 2, osize[1] / 2)
        obj.set_position(ssize[0] / 2 + xoff, ssize[1] / 2 + yoff)

    def go(self):
        self.stage.show_all()
        clutter.main()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    d = DinoCity((1280, 720), 'roms/', 'covers/')
    d.go()
