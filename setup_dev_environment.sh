#!/usr/bin/env sh

dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# Poetry is used for packaging and manage dependencies
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# Initial project setup on new machine, execute in new sub shell to get poetry loaded
(cd $dir/automata && poetry install)
(cd $dir/hub && poetry install)
