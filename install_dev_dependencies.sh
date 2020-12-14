#!/usr/bin/env sh

# PipX is used to install and run python applications in isolated environment
python3 -m pip install -U pipx
python3 -m pipx ensurepath
# Poetry is used for packaging and manage dependencies
pipx install poetry

pipx run poetry install
