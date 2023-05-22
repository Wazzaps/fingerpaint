import atexit
import sys
import threading
import gi

from fingerpaint.error_dialog import catch_errors, catch_errors_threaded
from fingerpaint.touchpad_locking import MockTouchpadLocker

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, Adw, GdkPixbuf, GObject, Gio
from fingerpaint.main_window import FingerpaintWindow
from fingerpaint.common import FatalError


class FingerpaintApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

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

    def on_activate(self, app):
        from fingerpaint.touchpad import Touchpad, MockTouchpad
        from fingerpaint.touchpad_locking import get_touchpad_locker

        win = None
        with catch_errors(self, win):
            is_dark = self.is_dark_theme()
            touchpad = Touchpad(width=600)
            touchpad_locker = get_touchpad_locker(touchpad.devname)

            # touchpad = MockTouchpad(width=600)
            # touchpad_locker = MockTouchpadLocker()

            self._load_css(
                """
                .shade-bg {
                    background-color: rgba(0, 0, 0, 0.4);
                }
                """,
            )

            win = FingerpaintWindow(
                application=app,
                width=touchpad.scaled_size[0],
                height=touchpad.scaled_size[1],
                fullscreen=False,
                title="Fingerpaint",
                hint="Press any key or click to finish drawing",
                hint_font_family="sans-serif",
                hint_font_size=16,
                hint_font_weight="bold",
                hint_font_color="#555555" if is_dark else "#aaaaaa",
                line_color="#cccccc" if is_dark else "#000000",
                output_file=None,
                touchpad_locker=touchpad_locker,
            )
            win.present()

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
        return (
            Gio.Settings.new("org.gnome.desktop.interface")["color-scheme"]
            == "prefer-dark"
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
    app = FingerpaintApp(application_id="com.github.wazzaps.Fingerpaint")
    app.run(sys.argv)
