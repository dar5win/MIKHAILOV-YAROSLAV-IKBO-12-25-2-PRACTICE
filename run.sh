#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then
    set -- --test --repository data/branch.json --package A --version 1.0.0
fi
exec python3 -m src.main "$@"
