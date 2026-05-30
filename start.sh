#!/bin/bash

set -e
python update.py
exec python -m bot
