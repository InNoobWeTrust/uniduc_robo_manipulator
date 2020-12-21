#!/usr/bin/env sh

dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

socat -d -d pty,raw,b9600,echo=0 EXEC:cat
