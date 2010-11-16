#!/usr/bin/env python

import clutter

BBOX_SIZE = (600, 436)  # Googled for chrono trigger cover art.

stage = clutter.Stage()
stage.set_size(1280,720)
stage.connect('destroy', clutter.main_quit)
stage.set_color(clutter.color_from_string("black"))

def on_key(stage, event):
    if event.keyval == clutter.keysyms.Escape:
        clutter.main_quit()
stage.connect('key-press-event', on_key)

label=clutter.Text()
label.set_text("Hello world lol")
label.set_color(clutter.color_from_string("white"))
stage.add(label)

bbox = clutter.Group()
bbox.set_position(100,100)
stage.add(bbox)

box = clutter.Rectangle()
box.set_position(-2,-2)
box.set_size(BBOX_SIZE[0]+4, BBOX_SIZE[1]+4)
box.set_color(clutter.color_from_string('black'))
box.set_border_color(clutter.color_from_string('blue'))
box.set_border_width(2)
bbox.add(box)

# cover = clutter.Texture(filename="chrono.jpg")
cover = clutter.Texture(filename="covers/simcity.jpg")
(w,h) = cover.get_size()
(wr,hr) = (w/BBOX_SIZE[0], h/BBOX_SIZE[1])
if wr > hr:
    cover.set_size(w/wr, h/wr)
else:
    cover.set_size(w/hr, h/hr)
    cover.set_position(w/hr/2, 0)
bbox.add(cover)

stage.show_all()
clutter.main()
