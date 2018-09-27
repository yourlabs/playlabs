FROM alpine:edge

ENV PYTHONIOENCODING UTF-8
ENV PYTHONUNBUFFERED 1

RUN apk update && apk --no-cache upgrade && apk add --no-cache git openssh-client py3-setuptools ansible && rm -rf /var/cache/apk/*

ONBUILD COPY . /app
ONBUILD RUN pip3 install -e /app

WORKDIR /app
