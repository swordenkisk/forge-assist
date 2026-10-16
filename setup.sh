#!/bin/sh
set -eu

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required."
    exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example. Add your provider settings."
else
    echo ".env already exists; leaving it unchanged."
fi

echo "Setup complete. Activate the environment with:"
echo "  . .venv/bin/activate"
