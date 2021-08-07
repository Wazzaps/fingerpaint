# FingerPaint

This utility lets you draw using your laptop's touchpad on Linux.

Pressing any key or clicking the touchpad will finish the drawing.

Your touchpad will not control the cursor while drawing, though external mice should still work.

No Wayland support at the moment, I need a simple `xinput disable ...` replacement.

## Video:

[![Video](http://img.youtube.com/vi/4gewfYs4I68/0.jpg)](http://www.youtube.com/watch?v=4gewfYs4I68 "FingerPaint demonstration video")

## Installation & Usage

```shell
pip3 install fingerpaint
```

```shell
# Simple usage
fingerpaint -o painting.png

# Play with style
fingerpaint --dark -o painting.png

# Copy to clipboard
fingerpaint --hint='Press any key or click to finish drawing'\n'Image will be copied to clipboard' -o - | xclip -sel clip -t image/png
```

## Install from source

Choose one of the following according to your distro:

- Ubuntu/Debian: `apt install xinput python3-pip python3-tk`
- [PRs welcome]

Then run: `pip3 install .` in the project directory 

## Uses

- Digitize your signature to sign PDFs
- Enter complex characters (e.g. Math symbols) or Asian scripts
- Doodle I guess
