FROM python:3

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install ffmpeg -y

COPY ./app/requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

ENV DATABASE_ENGINE='django.db.backends.sqlite3'
ENV DATABASE_NAME='/usr/src/app/data/db/ytmanager.db'
ENV DATABASE_HOST=''
ENV DATABASE_USERNAME=''
ENV DATABASE_PASSWORD=''
ENV DATABASE_PORT=''
ENV YOUTUBE_API_KEY='AIzaSyBabzE4Bup77WexdLMa9rN9z-wJidEfNX8'

VOLUME /usr/src/app/data/media
VOLUME /usr/src/app/data/db

COPY ./app/ .
COPY ./config/ ./config/