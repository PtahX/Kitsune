FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip nginx libpq-dev curl
RUN pip3 install uwsgi

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

COPY ./nginx.conf /etc/nginx/sites-enabled/default

ENV LANG=C.UTF-8

CMD service nginx start && uwsgi -s /tmp/kemono.sock --chmod-socket=666 --manage-script-name --mount /=server:app --processes 1 --threads 2 --master --listen 40000 --disable-logging --log-5xx