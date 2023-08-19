import os
import urllib.parse
from pathlib import Path
from typing import Optional, Callable

IS_SNAP_SANDBOXED = "SNAP" in os.environ
IS_FLATPAK_SANDBOXED = "FLATPAK_SANDBOX_DIR" in os.environ
IS_SANDBOXED = IS_SNAP_SANDBOXED or IS_FLATPAK_SANDBOXED


def get_output_file_path(
    callback: Callable[[Optional[Path]], None],
    default_file_name: str = "",
    window_title: str = "Save as...",
    parent_window: str = "",
):
    import gi
    from gi.repository import GLib, Gio

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    file_chooser = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.portal.FileChooser",
        None,
    )
    obj_id = file_chooser.call_sync(
        "SaveFile",
        GLib.Variant(
            "(ssa{sv})",
            (
                parent_window,  # parent_window
                window_title,  # title
                {  # options
                    "current_name": GLib.Variant("s", default_file_name),
                    "current_filter": GLib.Variant("(sa(us))", ("PNG Image", [(1, "image/png")])),
                },
            ),
        ),
        Gio.DBusCallFlags.NO_AUTO_START,
        500,
        None,
    )

    result_uri = None

    def on_response(*args):
        nonlocal result_uri
        params = args[5]
        retcode = params[0]
        if retcode == 0:
            result_uri = str(params[1]["uris"][0])
            assert result_uri.startswith("file://"), f"Unsupported URI: {result_uri}"
            callback(Path(urllib.parse.unquote(result_uri)[len("file://") :]))
        else:
            callback(None)
        bus.signal_unsubscribe(receiver)

    receiver = bus.signal_subscribe(
        None,
        "org.freedesktop.portal.Request",
        "Response",
        obj_id[0],
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
        None,
    )


if __name__ == "__main__":
    get_output_file_path(lambda p: print(p))
