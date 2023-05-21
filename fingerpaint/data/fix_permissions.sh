#!/usr/bin/env bash
set -e
echo 'ENV{ID_INPUT_TOUCHPAD}=="1", MODE="0664"' > /etc/udev/rules.d/99-touchpad-access.rules
udevadm control --reload-rules
udevadm trigger
if which snap > /dev/null; then
  snap connect fingerpaint:hardware-observe || true
  snap connect fingerpaint:raw-input || true
fi
echo 'Done! Run `fingerpaint` again.' 1>&2
