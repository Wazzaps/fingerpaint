# FingerPaint

[![PyPI link](https://img.shields.io/pypi/v/fingerpaint.svg)](https://pypi.python.org/pypi/fingerpaint/) [![Download count](https://pepy.tech/badge/fingerpaint)](https://pepy.tech/project/fingerpaint) [![License](https://img.shields.io/pypi/l/fingerpaint.svg)](https://pypi.python.org/pypi/fingerpaint/) [![Sponsor this project](https://img.shields.io/static/v1?label=Sponsor&logo=github-sponsors&logoColor=ffffff&color=777&message=This%20Project)](https://github.com/sponsors/Wazzaps)

This utility lets you draw using your laptop's touchpad on Linux.

Pressing any key or clicking the touchpad will finish the drawing.

Your touchpad will not control the cursor while drawing, though external mice should still work.

It has support for both X11 (all desktop environments), and Wayland (just Gnome at the moment).

## Video:

[![Video](http://img.youtube.com/vi/4gewfYs4I68/0.jpg)](http://www.youtube.com/watch?v=4gewfYs4I68 "FingerPaint demonstration video")

## Installation

### Ubuntu / Debian

```shell
sudo apt install libglib2.0-bin xinput python3-pip python3-tk
sudo pip3 install fingerpaint
sudo fingerpaint --fix-perms  # This command lets you run the utility without `sudo`
```

### Arch / Manjaro

If you are using X11, [Install `fingerpaint` via the AUR](https://aur.archlinux.org/packages/fingerpaint/).

If you are using Wayland, [Install `fingerpaint-wayland` via the AUR](https://aur.archlinux.org/packages/fingerpaint-wayland/).

### Nix (With Flakes)

```shell
nix profile install github:Wazzaps/fingerpaint
```

## Usage examples
```shell
# Simple usage
fingerpaint -o painting.png

# Play with style
fingerpaint --dark -o painting.png

# Copy to clipboard (using bash)
fingerpaint --hint=$'Press any key or click to finish drawing\nImage will be copied to clipboard' -o - | xclip -sel clip -t image/png

# Copy to clipboard (using fish)
fingerpaint --hint="Press any key or click to finish drawing"\n"Image will be copied to clipboard" -o - | xclip -sel clip -t image/png
```

## Uses

- Digitize your signature to sign PDFs
- Enter complex characters (e.g. Math symbols) or Asian scripts
- Doodle I guess
