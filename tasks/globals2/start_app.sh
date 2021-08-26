#!/bin/sh

FLASK_APP=app.py exec flask run --host=${HOST-127.0.0.1} --port=8000
