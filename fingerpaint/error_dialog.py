import contextlib
import traceback

import gi

from fingerpaint.common import FatalError

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject


@contextlib.contextmanager
def catch_errors(app, parent=None, do_finally=None):
    try:
        yield
    except FatalError as e:
        show_fatal_error(e.message, app, parent)
    except Exception as e:
        show_fatal_exception(e, app, parent)
    finally:
        if do_finally:
            do_finally()


@contextlib.contextmanager
def catch_errors_threaded(app, parent=None, do_finally=None):
    try:
        yield
    except FatalError as e:
        GObject.idle_add(show_fatal_error, e.message, app, parent)
    except Exception as e:
        GObject.idle_add(show_fatal_exception, e, app, parent)
    finally:
        if do_finally:
            do_finally()


def show_fatal_exception(e: Exception, app, parent=None):
    show_fatal_error(
        "Internal error:\n===============\n" + "".join(traceback.format_exception(e)),
        app,
        parent,
    )


def show_fatal_error(message: str, app, parent=None):
    if parent is None:
        parent = Adw.ApplicationWindow(application=app)
    dialog = Gtk.MessageDialog(
        title="Fingerpaint Error",
        text=message,
        modal=True,
        transient_for=parent,
        destroy_with_parent=True,
        buttons=Gtk.ButtonsType.CLOSE,
    )
    dialog_label = _gtk_get_child_by_buildable_id(dialog, "label")
    dialog_label.set_selectable(True)
    dialog.connect("response", lambda _dialog, response: app.quit())
    dialog.present()


def _gtk_get_child_by_buildable_id(widget, name):
    if isinstance(widget, Gtk.Buildable) and widget.get_buildable_id() == name:
        return widget
    else:
        for child in list(_gtk_get_children(widget)):
            result = _gtk_get_child_by_buildable_id(child, name)
            if result:
                return result
    return None


def _gtk_get_children(widget):
    child = widget.get_first_child()
    while child:
        yield child
        child = child.get_next_sibling()
