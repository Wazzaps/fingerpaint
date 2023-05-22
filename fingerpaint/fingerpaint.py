import atexit
import os
import sys
import threading
import gi
import subprocess as sp

from fingerpaint.common import FatalError
from fingerpaint.error_dialog import (
    catch_errors,
    catch_errors_threaded,
    show_fatal_error,
)
from fingerpaint.main_window import FingerpaintWindow
from fingerpaint.sandbox_utils import IS_SANDBOXED
from fingerpaint.touchpad_locking import MockTouchpadLocker

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, Adw, GdkPixbuf, GObject, Gio, GLib


class FingerpaintApp(Adw.Application):
    DEFAULT_WIDTH = 600

    def __init__(self, **kwargs):
        super().__init__(
            application_id="com.github.wazzaps.Fingerpaint",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs,
        )
        self.options = {}
        self.connect("activate", self.on_activate)

        self.add_main_option(
            long_name="width",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.INT,
            description=f"Width of the paint area (height is determined automatically) (default: {FingerpaintApp.DEFAULT_WIDTH})",
            arg_description="WIDTH",
        )

        self.add_main_option(
            long_name="height",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.INT,
            description="Height of the paint area (width is determined automatically)",
            arg_description="HEIGHT",
        )

        self.add_main_option(
            long_name="fullscreen",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.NONE,
            description="Make the canvas fullscreen",
            arg_description=None,
        )

        self.add_main_option(
            long_name="title",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Title of the window",
            arg_description="TITLE",
        )

        self.add_main_option(
            long_name="dark",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.NONE,
            description="Forces a dark theme",
            arg_description=None,
        )

        self.add_main_option(
            long_name="light",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.NONE,
            description="Forces a light theme",
            arg_description=None,
        )

        self.add_main_option(
            long_name="background",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Background color in #RRGGBB format, or other css background (default: depends on theme)",
            arg_description="COLOR",
        )

        self.add_main_option(
            long_name="hint",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Hint to display to user",
            arg_description="HINT",
        )

        self.add_main_option(
            long_name="hint-size",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.INT,
            description="Font size of the hint text (default: 16)",
            arg_description="SIZE",
        )

        self.add_main_option(
            long_name="hint-font",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Font family of the hint text (default: sans-serif)",
            arg_description="FONT",
        )

        self.add_main_option(
            long_name="hint-font-weight",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Font family weight of the hint text (one of: 'ultralight', 'light', 'normal', 'bold', 'ultrabold', 'heavy') (default: bold)",
            arg_description="WEIGHT",
        )

        self.add_main_option(
            long_name="hint-color",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Font color of the hint text in #RRGGBB format (default: depends on theme)",
            arg_description="COLOR",
        )

        self.add_main_option(
            long_name="line-color",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Line color in #RRGGBB format (default: depends on theme)",
            arg_description="COLOR",
        )

        self.add_main_option(
            long_name="line-thickness",
            short_name=0,
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.INT,
            description="Line thickness (default: 6)",
            arg_description="THICKNESS",
        )

        self.add_main_option(
            long_name="output",
            short_name=ord("o"),
            flags=GLib.OptionFlags.NONE,
            arg=GLib.OptionArg.STRING,
            description="Output file path (default: file chooser)",
            arg_description="PATH",
        )

    @staticmethod
    def _load_css(css_data: str):
        """
        Honestly what the fuck were you thinking, GTK, changing such an API without bumping your major version?
        """
        css_provider = Gtk.CssProvider()

        try:
            css_provider.load_from_data(
                css_data,
                -1,
            )
        except Exception as e:
            css_provider.load_from_data(css_data.encode())

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "width" in options and "height" in options:
            show_fatal_error(
                "Specify EITHER --width or --height, the other will be determined by touchpad size",
                self,
            )
            return 1

        if "light" in options and "dark" in options:
            show_fatal_error("Specify EITHER --light or --dark", self)
            return 1

        if options.get("output", None) not in ("-", None) and IS_SANDBOXED:
            show_fatal_error(
                "Cannot write to arbitrary file path in sandboxed mode\n"
                "Please either omit `--output` or use `--output=-` for stdout, then redirect the output to a file",
                self,
            )
            return 1

        self.options = options
        self.activate()
        return 0

    def on_activate(self, app):
        # I hate this too
        options = self.options
        self.options = {}

        with catch_errors(self):
            if options is None:
                options = {}

            if "width" not in options and "height" not in options:
                options["width"] = FingerpaintApp.DEFAULT_WIDTH

            self.validations()

            if "light" in options:
                Adw.StyleManager.get_default().set_color_scheme(
                    Adw.ColorScheme.FORCE_LIGHT
                )
                is_dark = False
            elif "dark" in options or self.is_dark_theme():
                Adw.StyleManager.get_default().set_color_scheme(
                    Adw.ColorScheme.FORCE_DARK
                )
                is_dark = True

            from fingerpaint.touchpad import Touchpad, MockTouchpad
            from fingerpaint.touchpad_locking import get_touchpad_locker

            touchpad = Touchpad(
                width=options.get("width", None),
                height=options.get("height", None),
            )
            touchpad_locker = get_touchpad_locker(touchpad.devname)

            # touchpad = MockTouchpad(
            #     width=options.get("width", None),
            #     height=options.get("height", None),
            # )
            # touchpad_locker = MockTouchpadLocker()

            self._load_css(
                f"""
                .shade-bg {{
                    background-color: rgba(0, 0, 0, 0.4);
                }}
                
                .fingerpaint-window-bg {{
                    background: {options.get("background", "rgba(0, 0, 0, 0)")};
                }}
                """,
            )

            default_font_color = "#555555" if is_dark else "#aaaaaa"
            default_line_color = "#cccccc" if is_dark else "#000000"

            win = FingerpaintWindow(
                application=app,
                width=touchpad.scaled_size[0],
                height=touchpad.scaled_size[1],
                fullscreen=options.get("fullscreen", False),
                title=options.get("title", "Fingerpaint"),
                hint=options.get("hint", "Press any key or click to finish drawing"),
                hint_font_family=options.get("hint-font", "sans-serif"),
                hint_font_size=options.get("hint-size", 16),
                hint_font_weight=options.get("hint-font-weight", "bold"),
                hint_font_color=options.get("hint-color", default_font_color),
                line_color=options.get("line-color", default_line_color),
                line_thickness=options.get("line-thickness", 6),
                output_file=options.get("output", None),
                touchpad_locker=touchpad_locker,
            )
            win.present()

        with catch_errors(self, win):

            def event_thread():
                touchpad_locker.lock()

                # Extra safety
                atexit.register(touchpad_locker.unlock)

                with catch_errors_threaded(
                    self,
                    win,
                    do_finally=lambda: touchpad_locker.unlock(),
                ):
                    # 0.007 seems smooth to me without losing too much precision
                    for lines in smooth_lines(touchpad.events, 0.007):
                        if lines:
                            win.hide_titlebar()
                            GObject.idle_add(win.draw_lines, lines)

                GObject.idle_add(win.save_and_quit)

            threading.Thread(target=event_thread, daemon=True).start()

    @staticmethod
    def is_dark_theme():
        interface = Gio.Settings.new("org.gnome.desktop.interface")
        try:
            color_scheme = interface["color-scheme"]
        except KeyError:
            color_scheme = ""

        try:
            gtk_theme = interface["gtk-theme"]
        except KeyError:
            gtk_theme = ""

        return color_scheme == "prefer-dark" or "dark" in gtk_theme.lower()

    @staticmethod
    def validations():
        if "XDG_SESSION_TYPE" not in os.environ:
            raise FatalError(
                'You don\'t seem to be running in a graphical environment ("XDG_SESSION_TYPE" is not set)'
            )

        if os.environ["XDG_SESSION_TYPE"] == "wayland":
            try:
                sp.check_output(["dconf", "help"])
            except sp.CalledProcessError:
                raise FatalError(
                    "`dconf` fails to run, it's required in Wayland based desktop environments"
                )
            except FileNotFoundError:
                raise FatalError(
                    "`dconf` binary not installed, install it with your package manager (Called `dconf-cli` on Ubuntu, or `dconf` on Arch)\n"
                    "It's required for Wayland based desktop environments."
                )
        else:
            try:
                sp.check_output(["xinput", "--version"])
            except sp.CalledProcessError:
                raise FatalError(
                    "`xinput` fails to run, it's required in X11 based desktop environments"
                )
            except FileNotFoundError:
                raise FatalError(
                    "`xinput` binary not installed, install it with your package manager (Called `xinput` on Ubuntu, or `xorg-xinput` on Arch)\n"
                    "It's required for X11 based desktop environments."
                )


def smooth_lines(events, smooth_radius):
    anchor = (-1, -1)
    for lines in events:
        new_lines = []
        for line in lines:
            if line == "jump":
                anchor = (-1, -1)
                continue

            if anchor == (-1, -1):
                anchor = line[0]
                new_lines.append(line)
            else:
                distance = (
                    (line[1][0] - anchor[0]) ** 2 + (line[1][1] - anchor[1]) ** 2
                ) ** 0.5
                if distance > smooth_radius:
                    new_lines.append((anchor, line[1]))
                    anchor = line[1]
        if new_lines:
            yield new_lines


def cli():
    app = FingerpaintApp()
    app.run(sys.argv)
