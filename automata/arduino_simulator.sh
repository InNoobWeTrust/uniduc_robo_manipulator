#!/usr/bin/env sh

dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Cleanup on exit
trap "rm $dir/pty.out >/dev/null 2>&1; exit" INT HUP QUIT TERM EXIT

# Ensure log file exist when on script start to start monitoring right away
touch $dir/pty.out

# To monitor, execute 'tail -f ./pty.out'
socat -d -d pty,link=$dir/pty,raw,b9600,echo=0 SYSTEM:"tee -a $dir/pty.out"
