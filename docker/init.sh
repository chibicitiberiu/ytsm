#!/bin/bash

./manage.py migrate
gunicorn -b 0.0.0.0:8000 -w 4 YtManager.wsgi
