#!/bin/sh

export PARH="$HOME/.local/bin:$PATH"
./dotenvx run -f .env -- uv run main.py