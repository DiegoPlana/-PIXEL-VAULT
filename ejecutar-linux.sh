#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "Se creara un entorno virtual y se instalaran las dependencias."
    read -r -p "Continuar? [s/N] " answer
    [[ "$answer" =~ ^[sS]$ ]] || exit 0
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python launcher.py
