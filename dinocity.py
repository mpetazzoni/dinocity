#!/usr/bin/env python

import clutter
import os
import struct

BBOX_SIZE = (600, 436)  # Googled for chrono trigger cover art.

# Let's pre-compute some Clutter colors
COLOR_WHITE = clutter.color_from_string('white')
COLOR_BLACK = clutter.color_from_string('black')
COLOR_BLUE = clutter.color_from_string('blue')
COLOR_RED = clutter.color_from_string('red')

# SMC ROM files may have an additional 512-byte SMC header at the beginning:
#   offset  size in bytes    contents
#  ----------------------------------------------------------------------------
#   0       2                ROM dump size, in units of 8kB (little-endian).
#   2       1                Binary flags for the ROM layout and save-RAM size.
#   3       509              All zero.

SMC_HEADER_SIZE = 512
SMC_ROM_LAYOUT_LOROM = 0x00
SMC_ROM_LAYOUT_HIROM = 0x30
SMC_SAVERAM_SIZE_32KB = 0x00
SMC_SAVERAM_SIZE_8KB = 0x04
SMC_SAVERAM_SIZE_4KB = 0x08
SMC_SAVERAM_SIZE_0kB = 0x0c

# SNES ROM headers are located at addresses 0x7fc0 for LoROM images and 0xffc0
# for HiROM images. These values may need to be offseted by 512 bytes when a
# SMC ROM header is present (respectively 0x81c0 and 0x101c0).
# See http://romhack.wikia.com/wiki/SNES_header for more information on SNES
# header fields and their values.

SNES_HEADER_SIZE = 64
SNES_HEADER_OFFSET_LOROM = 0x7fc0
SNES_HEADER_OFFSET_HIROM = 0xffc0

SNES_HEADER_FORMAT = '@21sBBBB'

SNES_ROM_LAYOUT_LOROM = 0x20
SNES_ROM_LAYOUT_HIROM = 0x21
SNES_ROM_LAYOUT_FASTROM = 0x10

SNES_CARTRIDGE_TYPE_ROM_ONLY = 0x00
SNES_CARTRIDGE_TYPE_SAVERAM = 0x02

class InvalidRomFileException(Exception):
    pass
class InvalidHeaderFormatException(Exception):
    pass

class Game:
    """
    This class defines a game, which is represented by its associated ROM file
    and accompanying cover art.
    """

    def __init__(self, filename, coverart='covers/_missing.png'):
        self.filename = filename
        self.cover = self._adjust_cover_size(
                clutter.Texture(filename=coverart),
                BBOX_SIZE)

        self.rom_info = self._parse_rom()
        print self.rom_info

    def _read_header_at(self, f, offset, has_smc_header=True):
        """Read and unpack the SNES header at the given offset, eventually
        taking into account the presence of an SMC header.
        """
        print ('Reading SNES header at offset %s (SMC header: %s)...' %
               (hex(offset), bool(has_smc_header)))

        try:
            f.seek(offset + has_smc_header*SMC_HEADER_SIZE)
            header = f.read(SNES_HEADER_SIZE)[:25]
            data = struct.unpack(SNES_HEADER_FORMAT, header)
            print 'Done:', data
            return data
        except struct.error:
            raise InvalidHeaderFormatException

        return None

    def _parse_rom(self):
        """Parses the ROM image to extract information from the SNES header
        (game title, ROM details, etc.).
        
        Returns a dictionary of information."""

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
            rom_info['cartridge_type'] = header_data[2]
            rom_info['rom_size'] = header_data[3]
            rom_info['ram_size'] = header_data[4]

        return rom_info


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

    def get_layout_type(self):
        layout = self.rom_info.get('layout', None)
        if layout == SNES_ROM_LAYOUT_LOROM:
            return 'LoROM'
        elif layout == SNES_ROM_LAYOUT_HIROM:
            return 'HiROM'
        elif layout == SNES_ROM_LAYOUT_FASTROM:
            return 'FastROM'
        return 'n/a'

    def get_cartridge_type(self):
        cartridge_type = self.rom_info.get('cartridge_type', None)
        if cartridge_type == SNES_CARTRIDGE_TYPE_ROM_ONLY:
            return 'ROM-only'
        elif cartridge_type == SNES_CARTRIDGE_TYPE_SAVERAM:
            return 'save-RAM'
        return 'n/a'

    def get_info_string(self):
        info = '%dkB %s' % (2**self.rom_info['rom_size'],
                            self.get_layout_type())
        if self.rom_info.get('cartridge_type', None) == SNES_CARTRIDGE_TYPE_SAVERAM:
            info += ', with %dkB %s' % (2**self.rom_info['ram_size'],
                                        self.get_cartridge_type())
        else:
            info += ', %s' % self.get_cartridge_type()

        return info

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
        info.set_text('%s (%s)' % (game.filename, game.get_info_string()))
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
