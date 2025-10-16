#!/bin/bash

cd $HOME/spapify  # Cloned repo directory

. $HOME/.local/bin/env  # Add 'uv', 'dotenvx' binary to PATH
dotenvx run -f .env -- uv run main.py
