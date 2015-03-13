# DinoCity. #

_You're lucky it doesn't have arms. Yet._

DinoCity aims at creating a full-screen graphical launcher for Super Nintendo ROMs, designed to be controlled with a SNES gamepad.

## Example ##

<img src='http://dinocity.googlecode.com/files/dinocity.jpg' width='100%' />

## Usage ##

### Preparation ###

Place your ROMs into a `roms/` directory, and the corresponding cover images using the same basename but with `.jpg` extension into the `covers/` directory. Then, run DinoCity:

```
$ cd dinocity/
$ ls roms/
simcity.smc  zelda.smc
$ ls covers/
simcity.jpg  zelda.jpg
$ ./dinocity
INFO:dinocity:DinoCity ready, 2 ROM(s).
```

### Keyboard usage ###

Once into DinoCity's graphical interface, the _Left_ and _Right_ keys can be used to browse through the available games. The _Enter_ key will run the currently selected game using the configured emulator (for now, you must have SNES9x installed).

Pressing _Escape_ at any time will exit the application.