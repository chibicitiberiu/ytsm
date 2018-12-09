FROM python:3

WORKDIR /usr/src/ytsm/app

# ffmpeg is needed for youtube-dl
RUN apt-get update
RUN apt-get install ffmpeg -y

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV YTSM_DEBUG='False'
ENV YTSM_DATA_PATH='/usr/src/ytsm/data'

VOLUME /usr/src/ytsm/config
VOLUME /usr/src/ytsm/data
VOLUME /usr/src/ytsm/download

COPY ./app/ ./
COPY ./docker/init.sh ./

EXPOSE 8000

CMD ["/bin/bash", "init.sh"]
