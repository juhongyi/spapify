#!/bin/bash

cd $HOME/spapify  # Cloned repo directory

for arg in "$@"; do
  case $arg in
    --job=*)
      JOB_NAME="${arg#*=}"
      ;;
  esac
done

. $HOME/.local/bin/env  # Add 'uv', 'dotenvx' binary to PATH
dotenvx run -f .env -- uv run main.py --job=$JOB_NAME
