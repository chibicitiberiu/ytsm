FROM python:3

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install ffmpeg -y

COPY ./app/requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

ENV YTSM_DATABASE_ENGINE='django.db.backends.sqlite3'
ENV YTSM_DATABASE_NAME='/usr/src/app/data/db/ytmanager.db'
ENV YTSM_DATABASE_HOST=''
ENV YTSM_DATABASE_USERNAME=''
ENV YTSM_DATABASE_PASSWORD=''
ENV YTSM_DATABASE_PORT=''
ENV YTSM_YOUTUBE_API_KEY='AIzaSyBabzE4Bup77WexdLMa9rN9z-wJidEfNX8'

VOLUME /usr/src/app/data/media
VOLUME /usr/src/app/data/db

COPY ./app/ .
COPY ./config/ ./config/

EXPOSE 8000

CMD ["/bin/bash ./init.sh"]