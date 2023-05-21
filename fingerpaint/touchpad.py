import math
import select
import sys
import time
import evdev
import pkg_resources
import pyudev
from typing import Optional
from fingerpaint.common import FatalError

fix_perms_script = pkg_resources.resource_filename(
    "fingerpaint", "data/fix_permissions.sh"
)


class Touchpad:
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None):
        self._touchpad = None
        udev = pyudev.Context()
        touchpad, self.devname = get_touchpad(udev)
        if touchpad is None:
            raise FatalError("No touchpad found")
        x_absinfo = touchpad.absinfo(evdev.ecodes.ABS_X)
        y_absinfo = touchpad.absinfo(evdev.ecodes.ABS_Y)
        val_range = (x_absinfo.max - x_absinfo.min, y_absinfo.max - y_absinfo.min)

        if width is not None:
            self.scaled_size = (width, int(width / val_range[0] * val_range[1]))
        else:
            self.scaled_size = (int(height / val_range[1] * val_range[0]), height)

        self._touchpad = touchpad
        self.events = self._handler_loop(x_absinfo, y_absinfo)

    def _handler_loop(self, x_absinfo, y_absinfo):
        last_pos = (-1, -1)
        curr_pos = (-1, -1)
        wip_pos = (-1, -1)
        while True:
            lines = []
            # Read all events
            while self._touchpad.fd in select.select([self._touchpad.fd], [], [], 0)[0]:
                event = self._touchpad.read_one()
                if event:
                    if event.type == evdev.ecodes.EV_ABS:
                        if event.code == evdev.ecodes.ABS_X:
                            wip_pos = (
                                (event.value - x_absinfo.min)
                                / (x_absinfo.max - x_absinfo.min),
                                wip_pos[1],
                            )
                        if event.code == evdev.ecodes.ABS_Y:
                            wip_pos = (
                                wip_pos[0],
                                (event.value - y_absinfo.min)
                                / (y_absinfo.max - y_absinfo.min),
                            )
                    if event.type == evdev.ecodes.EV_KEY:
                        if event.code == evdev.ecodes.BTN_TOUCH and event.value == 0:
                            wip_pos = (-1, -1)
                        if (
                            event.code == evdev.ecodes.BTN_LEFT
                            or event.code == evdev.ecodes.BTN_RIGHT
                        ) and event.value == 1:
                            return
                    if event.type == evdev.ecodes.EV_SYN:
                        curr_pos = wip_pos

                if last_pos != curr_pos:
                    if (
                        (last_pos[0] == -1 or last_pos[1] == -1)
                        and curr_pos[0] != -1
                        and curr_pos[1] != -1
                    ):
                        # Work with light taps
                        last_pos = curr_pos
                        lines.append("jump")
                    if (
                        last_pos[0] != -1
                        and last_pos[1] != -1
                        and curr_pos[0] != -1
                        and curr_pos[1] != -1
                    ):
                        lines.append((last_pos, curr_pos))
                    last_pos = curr_pos
            if lines:
                yield lines

            # Wait for new events
            select.select([self._touchpad.fd], [], [])

    def __del__(self):
        del self._touchpad


class MockTouchpad:
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None):
        self.devname = "MockTouchpad"
        val_range = [200, 100]

        def _handler_loop():
            yield []
            for x in range(200):
                y = math.sin(x / 100 * 2 * math.pi) * 50 + 50
                y2 = math.sin((x + 1) / 100 * 2 * math.pi) * 50 + 50
                yield [((x / 200, y / 100), ((x + 1) / 200, y2 / 100))]
                time.sleep(0.0001)

        if width is not None:
            self.scaled_size = (width, int(width / val_range[0] * val_range[1]))
        else:
            self.scaled_size = (int(height / val_range[1] * val_range[0]), height)

        self.events = _handler_loop()


def get_touchpad(udev):
    for device in get_touchpads(udev):
        dev_name = get_device_name(device).strip('"')
        print("Using touchpad:", dev_name, file=sys.stderr)
        try:
            return evdev.InputDevice(device.device_node), dev_name
        except PermissionError:
            permission_error()
    return None, None


def get_touchpads(udev):
    for device in udev.list_devices(ID_INPUT_TOUCHPAD="1"):
        if device.device_node is not None and device.device_node.rpartition("/")[
            2
        ].startswith("event"):
            yield device


def get_device_name(dev):
    while dev is not None:
        name = dev.properties.get("NAME")
        if name:
            return name
        else:
            dev = next(dev.ancestors, None)


def permission_error():
    raise FatalError(
        "Failed to access touchpad!\n"
        "To fix this, Please run the following command, then rerun fingerpaint:\n\n"
        f"sudo {fix_perms_script}"
    )
