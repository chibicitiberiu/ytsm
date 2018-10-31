FROM python:3

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install ffmpeg -y

COPY ./app/requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

ENV DATABASE_ENGINE='django.db.backends.postgresql'
ENV DATABASE_NAME='ytmanager.db'
ENV DATABASE_HOST='db'
ENV DATABASE_USERNAME='postgres'
ENV DATABASE_PASSWORD='postgres'
ENV DATABASE_PORT='5432'
ENV YOUTUBE_API_KEY='AIzaSyBabzE4Bup77WexdLMa9rN9z-wJidEfNX8'

COPY ./app/ .
COPY ./config/ ./config/