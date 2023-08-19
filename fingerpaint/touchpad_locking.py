import os
import subprocess as sp
from fingerpaint.common import FatalError


class TouchpadLocker:
    def __init__(self):
        self.locked = False

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False


class X11TouchpadLocker(TouchpadLocker):
    def __init__(self, devname: str):
        super().__init__()
        self.devname = devname

    def lock(self):
        sp.call(["xinput", "disable", self.devname])
        super().lock()

    def unlock(self):
        if not self.locked:
            return
        sp.call(["xinput", "enable", self.devname])
        super().unlock()


class GnomeWaylandTouchpadLocker(TouchpadLocker):
    def __init__(self):
        super().__init__()
        self.prev_value = None

    def lock(self):
        self.prev_value = sp.check_output(
            [
                "gsettings",
                "get",
                "org.gnome.desktop.peripherals.touchpad",
                "send-events",
            ]
        ).strip()

        # Fix for new gnome versions
        if self.prev_value == "":
            self.prev_value = "'enabled'"

        if self.prev_value not in (
            b"'enabled'",
            b"'disabled'",
            b"'disabled-on-external-mouse'",
        ):
            raise FatalError(
                f'Unexpected touchpad state: "{self.prev_value.decode()}", are you using Gnome?'
            )

        sp.call(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.peripherals.touchpad",
                "send-events",
                "'disabled'",
            ]
        )
        super().lock()

    def unlock(self):
        if not self.locked:
            return
        sp.call(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.peripherals.touchpad",
                "send-events",
                self.prev_value,
            ]
        )
        super().unlock()


class MockTouchpadLocker(TouchpadLocker):
    pass


def get_touchpad_locker(devname: str) -> TouchpadLocker:
    if os.environ["XDG_SESSION_TYPE"] == "wayland":
        return GnomeWaylandTouchpadLocker()
    else:
        return X11TouchpadLocker(devname)
