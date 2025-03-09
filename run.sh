#!/bin/bash

# run the website locally to check.


if [ -d ".venv" ]
then
    source .venv/bin/activate
    uv pip install -r requirements.txt
    python wsgi.py
else
    uv venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    python wsgi.py
fi
