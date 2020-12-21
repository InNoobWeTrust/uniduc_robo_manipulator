#!/usr/bin/env sh

require_root() {
    if test $(/usr/bin/id -u) -ne 0; then
        echo "Error: Must be root to run this script as it will install dependencies to the system" >&2
        exit 1
    fi
}

packages_needed='python3-pip python3-venv libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-tools python3-gi gir1.2-gstreamer-1.0 socat'

if [ -x "$(command -v brew)" ]; then yes | brew install gstreamer gst-devtools gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly python@3 pygobject3
elif [ -x "$(command -v apt)" ]; then require_root && yes | apt install $packages_needed
elif [ -x "$(command -v apt-get)" ]; then require_root && yes | apt-get install $packages_needed
elif [ -x "$(command -v pacman)" ]; then yes | pacman -S gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly python python-gobject
else echo "FAILED TO INSTALL PACKAGE: Supported package manager not found. You must manually install: $packages_needed" >&2; fi

