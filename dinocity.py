#!/usr/bin/env python

import clutter
import os
import struct

BBOX_SIZE = (600, 436)  # Googled for chrono trigger cover art.

COLOR_WHITE = clutter.color_from_string('white')
COLOR_BLACK = clutter.color_from_string('black')
COLOR_BLUE = clutter.color_from_string('blue')
COLOR_RED = clutter.color_from_string('red')

SMC_HEADER_SIZE = 512

SNES_HEADER_SIZE = 64
SNES_HEADER_OFFSET_LOROM = 0x7fc0
SNES_HEADER_OFFSET_HIROM = 0xffc0
SNES_HEADER_FORMAT = '@21sB'
SNES_ROM_LAYOUT_LOROM = 0x20
SNES_ROM_LAYOUT_HIROM = 0x21
SNES_ROM_LAYOUT_FASTROM = 0x10

class InvalidRomFileException(Exception):
    pass
class InvalidHeaderFormatException(Exception):
    pass

class Game:

    def __init__(self, filename, coverart='covers/_missing.png'):
        self.filename = filename
        self.cover = self._adjust_cover_size(
                clutter.Texture(filename=coverart),
                BBOX_SIZE)

        self.rom_info = self._parse_rom()
        print self.rom_info

    def _read_header_at(self, f, offset, has_smc_header):
        print ('Reading SNES header at offset %s (SMC header: %s)...' %
               (hex(offset), bool(has_smc_header)))

        try:
            f.seek(offset + has_smc_header*SMC_HEADER_SIZE)
            header = f.read(SNES_HEADER_SIZE)[:22]
            data = struct.unpack(SNES_HEADER_FORMAT, header)
            print 'Done:', data
            return data
        except struct.error:
            raise InvalidHeaderFormatException

        return None

    def _parse_rom(self):
        rom_info = {}
        with open(self.filename) as f:
            rom_info['size'] = os.fstat(f.fileno()).st_size
            rem = rom_info['size'] % 1024
            if rem == 0:
                rom_info['has_smc_header'] = False
            elif rem == 512:
                rom_info['has_smc_header'] = True
            else:
                raise InvalidRomFileException

            try:
                header_data = self._read_header_at(f, SNES_HEADER_OFFSET_LOROM,
                                                   rom_info['has_smc_header'])
            except InvalidHeaderFormatException:
                print 'Header does not match at LoROM offset.'
                print 'Trying at HiROM offset...'
                try:
                    header_data = self._read_header_at(f, SNES_HEADER_OFFSET_HIROM,
                                                       rom_info['has_smc_header'])
                except InvalidHeaderFormatException:
                    print 'Still no match at HiROM offset. Giving up.'
                    raise InvalidRomFileException

            rom_info['name'] = header_data[0].strip().title()
            rom_info['layout'] = header_data[1]

        return rom_info


    def _adjust_cover_size(self, texture, bbox):
        (w,h) = texture.get_size()
        (wr,hr) = (w/bbox[0], h/bbox[1])

        if wr > hr:
            texture.set_size(w/wr, h/wr)
        else:
            texture.set_size(w/hr, h/hr)
            texture.set_position(w/hr/2, 0)

        return texture

    def get_layout_type(self):
        layout = self.rom_info.get('layout', None)
        if layout == SNES_ROM_LAYOUT_LOROM:
            return 'LoROM'
        elif layout == SNES_ROM_LAYOUT_HIROM:
            return 'HiROM'
        elif layout == SNES_ROM_LAYOUT_FASTROM:
            return 'FastROM'
        return 'n/a'

class DinoCity:

    def __init__(self, screen_size, rom_directory, cover_directory):
        self.stage = self._create_stage(screen_size)
        self.rom_directory = rom_directory
        self.cover_directory = cover_directory

#        self._display_game('roms/zelda.smc', 'covers/zelda.jpg')
        self._display_game('roms/simcity.smc', 'covers/simcity.jpg')

    def _create_stage(self, screen_size):
        stage = clutter.Stage()
        stage.set_size(*screen_size)
        stage.connect('destroy', clutter.main_quit)
        stage.set_color(COLOR_BLACK)
        stage.connect('key-press-event', self._on_key_event)
        return stage

    def _on_key_event(self, stage, event):
        if event.keyval == clutter.keysyms.Escape:
            clutter.main_quit()

    def _display_game(self, filename, coverart=None):
        assert self.stage

        game = Game(filename, coverart)
        bbox = clutter.Group()
        bbox.set_position(100, 100)
        self.stage.add(bbox)

        box = clutter.Rectangle()
        box.set_position(-2,-2)
        box.set_size(BBOX_SIZE[0]+4, BBOX_SIZE[1]+4)
        box.set_color(COLOR_BLACK)
        box.set_border_color(COLOR_RED)
        box.set_border_width(2)
        bbox.add(box)

        name = clutter.Text()
        name.set_text(game.rom_info.get('name', 'Unknown'))
        name.set_position(BBOX_SIZE[0]+42, 0)
        name.set_color(COLOR_WHITE)
        name.set_font_name('Helvetica Bold 24')
        bbox.add(name)

        info = clutter.Text()
        info.set_text('%s (%.1f kB, %s)' % (game.filename,
                                            game.rom_info['size']/1024.0,
                                            game.get_layout_type()))
        info.set_position(BBOX_SIZE[0]+42, 50)
        info.set_color(COLOR_WHITE)
        info.set_font_name('Bitstream Vera Sans Mono Roman 10')
        bbox.add(info)

        bbox.add(game.cover)

    def go(self):
        self.stage.show_all()
        clutter.main()

if __name__ == '__main__':
    d = DinoCity((1280, 720), 'roms/', 'covers/')
    d.go()
