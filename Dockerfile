FROM python:3

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install ffmpeg -y

COPY ./app/requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app/ .
COPY ./config/ ./config/