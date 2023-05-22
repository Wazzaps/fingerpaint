import datetime
import threading
import gi
import cairo
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_escape
from fingerpaint.common import FatalError
from fingerpaint.error_dialog import (
    show_fatal_error,
    show_fatal_exception,
    catch_errors,
)
from fingerpaint.sandbox_utils import get_output_file_path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GdkPixbuf, GObject, GLib, Gio


class FingerpaintWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        width: int,
        height: int,
        fullscreen: bool,
        title: str,
        hint: str,
        hint_font_family: str,
        hint_font_size: float,
        hint_font_weight: str,
        hint_font_color: str,
        line_color: str,
        line_thickness: int,
        output_file: Optional[Path],
        touchpad_locker,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.hidden_titlebar = False
        self.shown_spinner = False
        self.output_file = output_file
        self.touchpad_locker = touchpad_locker

        # Sanitize parameters
        if '"' in hint_font_family or "\\" in hint_font_family:
            raise FatalError(
                "Font family must not contain double quotes or backslashes"
            )

        if hint_font_size < 0:
            raise FatalError("Font size must not be negative")

        if hint_font_weight not in (
            "ultralight",
            "light",
            "normal",
            "bold",
            "ultrabold",
            "heavy",
        ):
            raise FatalError(
                "Font weight must be one of 'ultralight', 'light', 'normal', 'bold', 'ultrabold', 'heavy'"
            )

        if (
            len(hint_font_color) != 7
            or hint_font_color[0] != "#"
            or not all(c in "0123456789abcdef" for c in hint_font_color[1:].lower())
        ):
            raise FatalError("Font color must be a hex color code with a leading '#'")

        if (
            len(line_color) != 7
            or line_color[0] != "#"
            or not all(c in "0123456789abcdef" for c in line_color[1:].lower())
        ):
            raise FatalError("Font color must be a hex color code with a leading '#'")

        self.line_color = (
            int(line_color[1:3].lower(), 16) / 255,
            int(line_color[3:5].lower(), 16) / 255,
            int(line_color[5:7].lower(), 16) / 255,
        )

        if line_thickness < 0:
            raise FatalError("Line thickness must not be negative")

        self.line_thickness = line_thickness

        # Set window properties
        self.set_title(title)
        self.set_modal(True)
        if fullscreen:
            self.fullscreen()
        else:
            self.set_default_size(width, height)
            self.set_resizable(False)

        # Header bar
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_valign(Gtk.Align.START)
        self.header_bar.add_css_class("flat")
        title_widget = Gtk.Label(label=title)
        title_widget.add_css_class("title")
        self.header_bar.set_title_widget(title_widget)
        self.title_revealer = Gtk.Revealer()
        self.title_revealer.set_reveal_child(True)
        self.title_revealer.set_child(self.header_bar)
        self.title_revealer.set_transition_duration(8000)

        # Saving spinner
        self.spinner_box = Gtk.Box()
        self.spinner_box.add_css_class("shade-bg")
        self.spinner = Gtk.Spinner()
        self.spinner.set_spinning(True)
        self.spinner.set_size_request(64, 64)
        self.spinner.set_valign(Gtk.Align.CENTER)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_hexpand(True)
        self.spinner_box.append(self.spinner)
        self.spinner_revealer = Gtk.Revealer()
        self.spinner_revealer.set_reveal_child(False)
        self.spinner_revealer.set_child(self.spinner_box)
        self.spinner_revealer.set_transition_duration(100)
        self.spinner_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)

        # Canvas
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.redraw)
        self.drawing_area.connect("resize", self.resized)
        self.visible_canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        if width / height > 16 / 9:
            output_width = int(width / height * 1080)
            output_height = 1080
        else:
            output_width = 1920
            output_height = int(height / width * 1920)
        self.output_canvas = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, output_width, output_height
        )

        # Hint
        hint_label = Gtk.Label(yalign=0.9)
        hint_label.set_markup(
            f"<span "
            f'face="{hint_font_family}" '
            f'size="{hint_font_size}pt" '
            f'weight="{hint_font_weight}" '
            f'color="{hint_font_color.lower()}">'
            f"{xml_escape(hint)}"
            f"</span>"
        )

        # Event handler
        event_controller = Gtk.EventControllerKey()

        def quit_on_keypress(_controller, _keyval, _keycode, _state):
            self.save_and_quit()

        event_controller.connect("key-pressed", quit_on_keypress)
        self.add_controller(event_controller)

        # All together
        overlay = Gtk.Overlay()
        overlay.add_css_class("fingerpaint-window-bg")
        overlay.add_overlay(hint_label)
        overlay.add_overlay(self.drawing_area)
        overlay.add_overlay(self.spinner_revealer)
        overlay.add_overlay(self.title_revealer)
        self.set_content(overlay)

    def resized(self, _canvas_widget, width, height):
        new_canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(new_canvas)
        ctx.scale(
            width / self.visible_canvas.get_width(),
            height / self.visible_canvas.get_height(),
        )
        ctx.set_source_surface(self.visible_canvas, 0, 0)
        ctx.paint()
        self.visible_canvas = new_canvas

    def draw_lines(self, lines):
        if self.shown_spinner:
            # Don't draw anything if the spinner is shown
            return
        ctx = cairo.Context(self.visible_canvas)
        ctx.set_source_rgb(*self.line_color)
        ctx.set_line_width(self.line_thickness)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        visible_canvas_width = self.visible_canvas.get_width()
        visible_canvas_height = self.visible_canvas.get_height()

        img_ctx = cairo.Context(self.output_canvas)
        img_ctx.set_source_rgb(0.0, 0.0, 0.0)
        img_ctx.set_line_width(20.0)
        img_ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        output_canvas_width = self.output_canvas.get_width()
        output_canvas_height = self.output_canvas.get_height()
        for line in lines:
            if line == "jump":
                continue
            x1, y1, x2, y2 = line[0][0], line[0][1], line[1][0], line[1][1]
            ctx.move_to(x1 * visible_canvas_width, y1 * visible_canvas_height)
            ctx.line_to(x2 * visible_canvas_width, y2 * visible_canvas_height)
            ctx.stroke()
            img_ctx.move_to(x1 * output_canvas_width, y1 * output_canvas_height)
            img_ctx.line_to(x2 * output_canvas_width, y2 * output_canvas_height)
            img_ctx.stroke()
        self.drawing_area.queue_draw()

    def hide_titlebar(self):
        if self.hidden_titlebar:
            return
        self.title_revealer.set_reveal_child(False)
        self.hidden_titlebar = True

    def show_spinner(self):
        if self.shown_spinner:
            return
        self.spinner_revealer.set_reveal_child(True)
        self.title_revealer.set_transition_duration(500)
        self.title_revealer.set_reveal_child(True)
        self.shown_spinner = True

    def redraw(self, _canvas_widget, ctx, width, height):
        ctx.scale(
            width / self.visible_canvas.get_width(),
            height / self.visible_canvas.get_height(),
        )
        ctx.set_source_surface(self.visible_canvas, 0, 0)
        ctx.paint()

    def save_and_quit(self):
        if self.shown_spinner:
            return
        with catch_errors(self.get_application(), self):
            self.touchpad_locker.unlock()
            self.show_spinner()

            def actually_save_file(path: Optional[Path]):
                if path:
                    if path == "-":
                        self.output_canvas.write_to_png("/dev/stdout")
                    else:
                        self.output_canvas.write_to_png(str(path))
                GObject.idle_add(self.get_application().quit)

            if self.output_file:
                threading.Thread(
                    target=actually_save_file,
                    args=(self.output_file,),
                ).start()
            else:
                # if IS_SANDBOXED:
                get_output_file_path(
                    actually_save_file,
                    default_file_name=f"Painting {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.png",
                    window_title="Save painting...",
                )
                # self._broken_native_file_chooser(actually_save_file)
                # else:
                #     self._gtk_file_chooser(actually_save_file)

    def _gtk_file_chooser(self, callback):
        # Doesn't work in sandbox
        pass
        # file_chooser = Gtk.FileChooserDialog(
        #     title="Save painting...",
        #     action=Gtk.FileChooserAction.SAVE,
        # )
        # file_chooser.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        # file_chooser.add_button("_Save", Gtk.ResponseType.OK)
        #
        # def file_chooser_response(dialog, response):
        #     dialog.hide()
        #     if response == Gtk.ResponseType.OK:
        #         file_path = dialog.get_file().get_path()
        #         threading.Thread(
        #             target=callback,
        #             args=(Path(file_path),),
        #         ).start()
        #     else:
        #         GObject.idle_add(self.get_application().quit)
        #
        # file_chooser.set_transient_for(self)
        # file_chooser.connect("response", file_chooser_response)
        # file_chooser.set_current_name(
        #     f"Painting {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.png"
        # )
        # file_chooser.set_current_folder(
        #     Gio.File.new_for_path(str(Path.home() / "Pictures"))
        # )
        # file_chooser.set_modal(True)
        # file_chooser.show()

    def _broken_native_file_chooser(self, callback):
        # Doesn't work outside sandbox
        pass
        # file_chooser = Gtk.FileChooserNative.new(
        #     title="Save as...",
        #     parent=self,
        #     action=Gtk.FileChooserAction.SAVE,
        #     accept_label=None,
        #     cancel_label=None,
        # )
        #
        # def file_dialog_response(dialog, response):
        #     if response == Gtk.ResponseType.ACCEPT:
        #         print(dialog.get_file().get_path())
        #         print(dialog.get_filename())
        #         # threading.Thread(
        #         #     target=actually_save_file,
        #         #     args=(Path(dialog.get_filename()),),
        #         # ).start()
        #     else:
        #         GObject.idle_add(self.get_application().quit)
        #
        # file_chooser.set_transient_for(self)
        # file_chooser.connect("response", file_dialog_response)
        # file_chooser.set_current_name(
        #     f"Painting {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.png"
        # )
        # file_chooser.set_modal(True)
        # file_chooser.show()

    def _broken_new_file_chooser(self):
        # Doesn't work on versions that actually exist
        pass
        # file_dialog = Gtk.FileDialog.new()
        #
        # def file_dialog_response(dialog, result):
        #     with catch_errors(self.get_application(), self):
        #         try:
        #             file = dialog.save_finish(result)
        #             if file is not None:
        #                 print(f"File path is {file.get_path()}")
        #         except GLib.Error as e:
        #             show_fatal_error(
        #                 f"Error opening file: {e.message}",
        #                 self.get_application(),
        #                 self,
        #             )
        #
        #     # if response == Gtk.ResponseType.ACCEPT:
        #     #     threading.Thread(
        #     #         target=actually_save_file,
        #     #         args=(Path(dialog.get_filename()),),
        #     #     ).start()
        #     # else:
        #     #     GObject.idle_add(self.get_application().quit)
        #
        # file_dialog.connect("response", file_dialog_response)
        # # file_dialog.set_transient_for(self)
        # file_dialog.set_modal(True)
        # # file_dialog.set_select_multiple(False)
        # # file_dialog.set_action(Gtk.FileChooserAction.SAVE)
        # # file_dialog.set_do_overwrite_confirmation(True)
        # file_dialog.set_initial_name(
        #     f"Painting {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.png"
        # )
        # file_dialog.set_initial_folder("~/Pictures")
        # file_dialog.save(
        #     parent=self,
        #     cancellable=None,
        #     callback=file_dialog_response,
        # )
