#!/usr/bin/env python3
import _tkinter
import argparse
import contextlib
import os
import pkg_resources
import subprocess as sp
import sys
import tkinter
import tkinter.font
import PIL.Image
import PIL.ImageDraw
import evdev
import pyudev
from fingerpaint.sandbox_utils import GSETTINGS_SCHEMA_DIR_PARAM, get_output_file_path, IS_SANDBOXED
from io import BytesIO

DEFAULT_WIDTH = 600
AA_FACTOR = 4  # Anti-aliasing
OUTPUT_SCALE = 2

fix_perms_script = pkg_resources.resource_filename('fingerpaint', 'data/fix_permissions.sh')


@contextlib.contextmanager
def lock_pointer_x11(devname):
    sp.call(['xinput', 'disable', devname])
    try:
        yield
    finally:
        sp.call(['xinput', 'enable', devname])


@contextlib.contextmanager
def lock_pointer_wayland():
    prev_value = sp.check_output(
        ['gsettings'] +
        GSETTINGS_SCHEMA_DIR_PARAM +
        ['get', 'org.gnome.desktop.peripherals.touchpad', 'send-events']
    ).strip()

    # Fix for arch based distros
    if prev_value == '':
        prev_value = "'enabled'"

    if prev_value not in (b"'enabled'", b"'disabled'", b"'disabled-on-external-mouse'"):
        print(f'Unexpected touchpad state: "{prev_value.decode()}", are you using Gnome?', file=sys.stderr)
        exit(1)

    sp.call(['dconf', 'write', '/org/gnome/desktop/peripherals/touchpad/send-events', "'disabled'"])
    try:
        yield
    finally:
        sp.call(['dconf', 'write', '/org/gnome/desktop/peripherals/touchpad/send-events', prev_value])


def make_ui(events, image_size, devname, args):
    top = tkinter.Tk()

    if args.fullscreen:
        top.attributes('-fullscreen', True)
        top.update()
        window_size = top.winfo_width(), top.winfo_height()
    else:
        top.resizable(False, False)
        window_size = image_size

    top.title(args.title)

    def exit_handler(_):
        top.destroy()

    top.bind('<Key>', exit_handler)
    top.bind('<Button>', exit_handler)

    hint_font = tkinter.font.Font(family=args.hint_font,
                                  size=args.hint_size, weight=args.hint_font_weight)

    canvas = tkinter.Canvas(top, bg=args.background, height=window_size[1], width=window_size[0], borderwidth=0, highlightthickness=0)
    canvas.create_text(
        (window_size[0] / 2, window_size[1] * 9 / 10), fill=args.hint_color, font=hint_font, justify=tkinter.CENTER,
        text=args.hint
    )
    aa_factor = AA_FACTOR * OUTPUT_SCALE
    image = PIL.Image.new("RGBA", (image_size[0] * aa_factor, image_size[1] * aa_factor), (0, 0, 0, 0))
    image_canvas = PIL.ImageDraw.Draw(image)

    canvas.pack(fill=tkinter.BOTH, expand=True)
    try:
        if os.environ['XDG_SESSION_TYPE'] == 'wayland':
            lock_pointer = lock_pointer_wayland()
        else:
            lock_pointer = lock_pointer_x11(devname)

        with lock_pointer:
            while True:
                lines = next(events)
                for line in lines:
                    screen_projected_start = (line[0][0] * window_size[0], line[0][1] * window_size[1])
                    screen_projected_end = (line[1][0] * window_size[0], line[1][1] * window_size[1])
                    image_projected_start = (line[0][0] * image_size[0], line[0][1] * image_size[1])
                    image_projected_end = (line[1][0] * image_size[0], line[1][1] * image_size[1])
                    canvas.create_line(
                        screen_projected_start, screen_projected_end,
                        width=args.line_thickness, capstyle=tkinter.ROUND, fill=args.line_color
                    )
                    image_canvas.line(
                        ((int(image_projected_start[0] * aa_factor), int(image_projected_start[1] * aa_factor)),
                         (int(image_projected_end[0] * aa_factor), int(image_projected_end[1] * aa_factor))),
                        width=int(args.line_thickness * aa_factor), joint='curve', fill=(0, 0, 0)
                    )
                    offset = (args.line_thickness * aa_factor - 1) / 2
                    image_canvas.ellipse(
                        (int(image_projected_start[0] * aa_factor - offset), int(image_projected_start[1] * aa_factor - offset),
                         int(image_projected_start[0] * aa_factor + offset), int(image_projected_start[1] * aa_factor + offset)),
                        fill=(0, 0, 0)
                    )
                    image_canvas.ellipse(
                        (int(image_projected_end[0] * aa_factor - offset), int(image_projected_end[1] * aa_factor - offset),
                         int(image_projected_end[0] * aa_factor + offset), int(image_projected_end[1] * aa_factor + offset)),
                        fill=(0, 0, 0)
                    )

                top.update_idletasks()
                top.update()
    except (KeyboardInterrupt, _tkinter.TclError):
        del events

        image = image.resize((image_size[0] * OUTPUT_SCALE, image_size[1] * OUTPUT_SCALE), resample=PIL.Image.LANCZOS)
        if args.output is None:
            path = get_output_file_path(window_title="Save image")
            if path:
                print('Writing output to', path.name, file=sys.stderr)
                image.save(str(path), format='png')
            else:
                print('Save was canceled', file=sys.stderr)
        elif args.output == '-':
            print('Writing output to stdout', file=sys.stderr)
            with BytesIO() as temp_buf:
                image.save(temp_buf, format='png')
                sys.stdout.buffer.write(temp_buf.getvalue())
        else:
            print('Writing output to', args.output, file=sys.stderr)
            image.save(args.output, format='png')
        exit(0)


def get_touchpads(udev):
    for device in udev.list_devices(ID_INPUT_TOUCHPAD='1'):
        if device.device_node is not None and device.device_node.rpartition('/')[2].startswith('event'):
            yield device


def get_device_name(dev):
    while dev is not None:
        name = dev.properties.get('NAME')
        if name:
            return name
        else:
            dev = next(dev.ancestors, None)


def permission_error():
    if sys.stdin.isatty() and not IS_SANDBOXED:
        print('Touchpad access is currently restricted. Would you like to unrestrict it?', file=sys.stderr)
        response = input('[Yes]/no: ')
        if response.lower() in ('y', 'ye', 'yes', 'ok', 'sure', ''):
            sp.call(['pkexec', fix_perms_script])
        else:
            print('Canceled.', file=sys.stderr)
    else:
        print('Failed to access touchpad!', file=sys.stderr)
        print('To fix this, Please run the following commands, then rerun fingerpaint:', file=sys.stderr)
        print('''  echo 'ENV{ID_INPUT_TOUCHPAD}=="1", MODE="0664"' | sudo tee /etc/udev/rules.d/99-touchpad-access.rules''', file=sys.stderr)
        print('  sudo udevadm control --reload-rules', file=sys.stderr)
        print('  sudo udevadm trigger', file=sys.stderr)

    exit(1)


def get_touchpad(udev):
    for device in get_touchpads(udev):
        dev_name = get_device_name(device).strip('"')
        print('Using touchpad:', dev_name, file=sys.stderr)
        try:
            return evdev.InputDevice(device.device_node), dev_name
        except PermissionError:
            permission_error()
    return None, None


def main(args):
    udev = pyudev.Context()
    touchpad, devname = get_touchpad(udev)
    if touchpad is None:
        print('No touchpad found', file=sys.stderr)
        exit(1)
    x_absinfo = touchpad.absinfo(evdev.ecodes.ABS_X)
    y_absinfo = touchpad.absinfo(evdev.ecodes.ABS_Y)
    val_range = (x_absinfo.max - x_absinfo.min, y_absinfo.max - y_absinfo.min)

    def handler_loop():
        last_pos = (-1, -1)
        curr_pos = (-1, -1)
        wip_pos = (-1, -1)
        while True:
            event = touchpad.read_one()
            if event:
                if event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_X:
                        wip_pos = ((event.value - x_absinfo.min) / (x_absinfo.max - x_absinfo.min), wip_pos[1])
                    if event.code == evdev.ecodes.ABS_Y:
                        wip_pos = (wip_pos[0], (event.value - y_absinfo.min) / (y_absinfo.max - y_absinfo.min))
                if event.type == evdev.ecodes.EV_KEY:
                    if event.code == evdev.ecodes.BTN_TOUCH and event.value == 0:
                        wip_pos = (-1, -1)
                    if (event.code == evdev.ecodes.BTN_LEFT or event.code == evdev.ecodes.BTN_RIGHT) \
                            and event.value == 1:
                        raise KeyboardInterrupt()
                if event.type == evdev.ecodes.EV_SYN:
                    curr_pos = wip_pos

            if last_pos != curr_pos:
                if (last_pos[0] == -1 or last_pos[1] == -1) and curr_pos[0] != -1 and curr_pos[1] != -1:
                    # Work with light taps
                    last_pos = curr_pos
                if last_pos[0] != -1 and last_pos[1] != -1 and curr_pos[0] != -1 and curr_pos[1] != -1:
                    yield [(last_pos, curr_pos)]
                else:
                    yield []
                last_pos = curr_pos
            else:
                yield []

    if args.width is not None:
        scaled = (args.width, int(args.width / val_range[0] * val_range[1]))
    else:
        scaled = (int(args.height / val_range[1] * val_range[0]), args.height)

    make_ui(handler_loop(), scaled, devname, args)
    del touchpad


def validations():
    if 'XDG_SESSION_TYPE' not in os.environ:
        print('You don\'t seem to be running in a graphical environment ("XDG_SESSION_TYPE" is not set)')
        exit(1)

    if os.environ['XDG_SESSION_TYPE'] == 'wayland':
        try:
            sp.check_output(['dconf', 'help'])
        except sp.CalledProcessError:
            print('`dconf` fails to run, it\'s required in Wayland based desktop environments', file=sys.stderr)
            exit(1)
        except FileNotFoundError:
            print('`dconf` binary not installed, install it with your package manager (Called `dconf-cli` on Ubuntu, or `dconf` on Arch)', file=sys.stderr)
            print('It\'s required for Wayland based desktop environments.', file=sys.stderr)
            exit(1)
    else:
        try:
            sp.check_output(['xinput', '--version'])
        except sp.CalledProcessError:
            print('`xinput` fails to run, it\'s required in X11 based desktop environments', file=sys.stderr)
            exit(1)
        except FileNotFoundError:
            print('`xinput` binary not installed, install it with your package manager (Called `xinput` on Ubuntu, or `xorg-xinput` on Arch)', file=sys.stderr)
            print('It\'s required for X11 based desktop environments.', file=sys.stderr)
            exit(1)

    pillow_version = PIL.__version__.split('.')
    pillow_version = int(pillow_version[0]), int(pillow_version[1])
    if pillow_version[0] < 5 or (pillow_version[0] == 5 and pillow_version[1] < 3):
        print('Pillow version 5.3.0 or higher is required', file=sys.stderr)
        print('Please run:  python3 -m pip install -U Pillow', file=sys.stderr)
        exit(1)


def cli():
    parser = argparse.ArgumentParser(description='Gets a finger painting from the user using the touchpad, useful for '
                                                 'document signatures or complex character input, etc.')
    parser.add_argument(
        '--width', type=int,
        help=f'Width of the paint area (height is determined automatically) (default: {DEFAULT_WIDTH})'
    )
    parser.add_argument(
        '--height', type=int,
        help='Height of the paint area (width is determined automatically)'
    )
    parser.add_argument(
        '--fullscreen', action='store_true',
        help='Make the canvas fullscreen'
    )
    parser.add_argument(
        '--title', type=str, default='FingerPaint',
        help='Title of the window'
    )
    parser.add_argument(
        "--dark", action='store_true',
        help='Changes `background`, `hint-color`, and `line-color` to a dark theme')
    parser.add_argument(
        '--background', type=str, default='#eeeeee',
        help='Background color (default: light gray)'
    )
    parser.add_argument(
        '--hint', type=str, default='Press any key or click to finish drawing',
        help='Hint to display to user'
    )
    parser.add_argument(
        '--hint-size', type=int, default=16,
        help='Font size of the hint text (default: 16)'
    )
    parser.add_argument(
        '--hint-font', type=str, default='Ubuntu',
        help='Font family of the hint text (default: Ubuntu)'
    )
    parser.add_argument(
        '--hint-font-weight', type=str, default='bold',
        help='Font family weight of the hint text (default: bold)'
    )
    parser.add_argument(
        '--hint-color', type=str, default='#aaaaaa',
        help='Font color of the hint text (default: dark gray)'
    )
    parser.add_argument(
        '--line-color', type=str, default='#000000',
        help='Line color (default: black)'
    )
    parser.add_argument(
        '--line-thickness', type=int, default=6,
        help='Line thickness (default: 6)'
    )
    parser.add_argument(
        '-o', '--output', type=str,
        help='Output file path'
    )
    args = parser.parse_args()

    if args.dark:
        args.background = '#222222'
        args.line_color = '#cccccc'
        args.hint_color = '#555555'

    if args.width is not None and args.height is not None:
        print('Specify EITHER --width or --height, the other will be determined by touchpad size', file=sys.stderr)
        exit(1)

    if args.width is None and args.height is None:
        args.width = DEFAULT_WIDTH

    if args.output not in ('-', None) and IS_SANDBOXED:
        print('Cannot write to arbitrary file path in sandboxed mode', file=sys.stderr)
        print("Please either omit `--output` or use `--output=-` for stdout if you know what you're doing", file=sys.stderr)
        exit(1)

    validations()

    main(args)
