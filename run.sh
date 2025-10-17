#!/bin/bash

DOTENV_FILE=".env"
JOB_NAME="refresh_access_token"

for arg in "$@"; do
  case $arg in
    --job=*)
      JOB_NAME="${arg#*=}"
      ;;
    --dotenv-file=*)
      DOTENV_FILE="${arg#*=}"
      ;;
  esac
done

. $HOME/.local/bin/env  # Add 'uv', 'dotenvx' binary to PATH
cd $HOME/spapify  # Cloned repo directory
dotenvx run -f $DOTENV_FILE -- uv run main.py --job=$JOB_NAME
