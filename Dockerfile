FROM alpine:edge

ENV PYTHONIOENCODING UTF-8
ENV PYTHONUNBUFFERED 1

RUN apk update && apk --no-cache upgrade && apk add --no-cache openssh-client py3-setuptools ansible sshpass && rm -rf /var/cache/apk/* && pip3 install -U pip

RUN mkdir -p /app
ADD requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt
ADD . /app
RUN pip3 install --no-deps -e /app

WORKDIR /app
