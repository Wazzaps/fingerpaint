# FingerPaint

This utility lets you draw using your laptop's touchpad on Linux.

Pressing any key or clicking the touchpad will finish the drawing.

Your touchpad will not control the cursor while drawing, though external mice should still work.

It has support for both X11 (all desktop environments), and Wayland (just Gnome at the moment).

## Video:

[![Video](http://img.youtube.com/vi/4gewfYs4I68/0.jpg)](http://www.youtube.com/watch?v=4gewfYs4I68 "FingerPaint demonstration video")

## Installation

### Ubuntu / Debian

```shell
apt install xinput python3-pip python3-tk
pip3 install fingerpaint
```

### Arch / Manjaro

[Install `fingerpaint` via the AUR](https://aur.archlinux.org/packages/fingerpaint/)

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
