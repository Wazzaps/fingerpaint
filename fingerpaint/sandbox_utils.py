import os
from pathlib import Path
from typing import Optional

IS_SANDBOXED = "SNAP" in os.environ

if IS_SANDBOXED:
    GSETTINGS_SCHEMA_DIR_PARAM = [
        "--schemadir",
        os.environ["SNAP"] + "/usr/share/glib-2.0/schemas",
    ]

else:
    GSETTINGS_SCHEMA_DIR_PARAM = []


def get_output_file_path(window_title="Save file", parent_window="") -> Optional[Path]:
    import dbus.mainloop.glib
    import gi.repository.GLib

    glib_mainloop = gi.repository.GLib.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    file_chooser = dbus.Interface(
        bus.get_object(
            "org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop", introspect=False,
        ),
        "org.freedesktop.portal.FileChooser",
    )

    obj_id = file_chooser.SaveFile(
        parent_window,  # parent_window
        window_title,  # title
        {  # options
            "current_name": "Untitled.png",
            "current_filter": ("PNG Image", [(dbus.UInt32(1), "image/png")]),
        },
        signature="ssa{sv}",
    )

    result_uri = None

    def on_response(result, d):
        nonlocal result_uri
        glib_mainloop.quit()
        receiver.remove()
        if result == 0:
            result_uri = str(d["uris"][0])

    receiver = bus.add_signal_receiver(
        on_response,
        "Response",
        "org.freedesktop.portal.Request",
        None,
        obj_id,
    )

    glib_mainloop.run()

    if result_uri:
        assert result_uri.startswith("file://"), f"Unsupported URI: {result_uri}"
        result_uri = Path(result_uri[len("file://") :])

    return result_uri


if __name__ == '__main__':
    print(get_output_file_path())
