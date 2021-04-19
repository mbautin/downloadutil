#!/usr/bin/env bash

. venv/bin/activate
set -euo pipefail
cd "${BASH_SOURCE[0]%/*}"/..
codecheck "$@"
