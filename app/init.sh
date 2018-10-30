#!/bin/bash

#./manage.py runserver 0.0.0.0:8000 --noreload
gunicorn -b 0.0.0.0:8000 -w 4 YtManager.wsgi
