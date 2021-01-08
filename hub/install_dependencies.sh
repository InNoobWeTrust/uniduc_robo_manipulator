#!/usr/bin/env sh

require_root() {
    if test $(/usr/bin/id -u) -ne 0; then
        echo "Error: Must be root to run this script as it will install dependencies to the system" >&2
        exit 1
    fi
}

packages_needed='redis'

if [ -x "$(command -v brew)" ]; then yes | brew install $packages_needed
elif [ -x "$(command -v apt)" ]; then require_root && yes | apt install $packages_needed
elif [ -x "$(command -v apt-get)" ]; then require_root && yes | apt-get install $packages_needed
elif [ -x "$(command -v pacman)" ]; then yes | pacman -S $packages_needed
else echo "FAILED TO INSTALL PACKAGE: Supported package manager not found. You must manually install: $packages_needed" >&2; fi

