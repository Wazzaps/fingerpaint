# FingerPaint

This utility lets you draw using your laptop's touchpad on Linux.

Pressing any key or clicking the touchpad will finish the drawing.

Your touchpad will not control the mouse while drawing, though external mice should still work.

No Wayland support at the moment, I need a simple `xinput disable ...` replacement.

## Video:

[![Video](http://img.youtube.com/vi/4gewfYs4I68/0.jpg)](http://www.youtube.com/watch?v=4gewfYs4I68 "FingerPaint demonstration video")

## Installation

```shell
pip install fingerpaint
```

## Install from source

Choose one of the following according to your distro:

- Ubuntu/Debian: `apt install xinput python3-pip python3-tk`
- [PRs welcome]

Then run: `pip install .` in the project directory 

## Uses

- Digitize your signature to sign PDFs
- Enter complex characters (e.g. Math symbols) or Asian scripts
- Doodle I guess
