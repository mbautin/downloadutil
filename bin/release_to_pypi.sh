#!/usr/bin/env bash

export TWINE_USERNAME=yugabyte

set -euo pipefail -x
cd "${BASH_SOURCE[0]%/*}"/..

rm -f dist/*
make sdist
venv/bin/python3 -m twine upload dist/*
