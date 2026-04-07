#!/bin/bash

echo "setting up virtual env"

python3 -m venv .venv

source .venv/bin/activate

echo "installing dependencies"
pip install -r requirements.txt

echo "run 'source .venv/bin/activate' to activate"