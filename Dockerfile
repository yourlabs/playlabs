FROM alpine:edge

ENV PYTHONIOENCODING UTF-8
ENV PYTHONUNBUFFERED 1

RUN apk update && apk --no-cache upgrade && apk add --no-cache openssh-client py3-setuptools ansible && rm -rf /var/cache/apk/* && pip3 install -U pip

RUN mkdir -p /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -Ur /app/requirements.txt
COPY . /app
RUN pip3 install -e /app

WORKDIR /app
