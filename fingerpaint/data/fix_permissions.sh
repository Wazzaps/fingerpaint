#!/usr/bin/env bash
set -e
echo 'ENV{ID_INPUT_TOUCHPAD}=="1", MODE="0664"' > /etc/udev/rules.d/99-touchpad-access.rules
udevadm control --reload-rules
udevadm trigger
echo 'Done! Run `fingerpaint` again.' 1>&2