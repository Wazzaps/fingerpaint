# FingerPaint

This utility lets you draw using your laptop's touchpad on Linux.

Pressing any key or clicking the touchpad will finish the drawing.

Your touchpad will not control the cursor while drawing, though external mice should still work.

No Wayland support at the moment, I need a simple `xinput disable ...` replacement.

## Video:

[![Video](http://img.youtube.com/vi/4gewfYs4I68/0.jpg)](http://www.youtube.com/watch?v=4gewfYs4I68 "FingerPaint demonstration video")

## Installation & Usage

- Via pip:

```shell
pip3 install fingerpaint
```

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
- Arch Linux / Manjaro:

You can install the package via the AUR: [fingerpaint](https://aur.archlinux.org/packages/fingerpaint/)

```shell
git clone https://aur.archlinux.org/fingerpaint.git
cd fingerpaint
makepkg -sic
```

## Install from source

Clone the repo, then manually install via `python setup.py install`. Alternatively, you can use `pip3` to install the local files, shown here for Ubuntu:
`apt install xinput python3-pip python3-tk`, then run: `pip3 install .` in the project directory 

## Uses

- Digitize your signature to sign PDFs
- Enter complex characters (e.g. Math symbols) or Asian scripts
- Doodle I guess
