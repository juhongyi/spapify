#!/bin/sh

cd $HOME/spapify
export PATH="$HOME/.local/bin:$PATH"
./dotenvx run -f .env -- uv run main.py