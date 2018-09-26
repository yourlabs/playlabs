FROM python:3-alpine

ENV PYTHONIOENCODING UTF-8
ENV PYTHONUNBUFFERED 1

RUN apk update && apk --no-cache upgrade && apk --no-cache add shadow python3 bash git curl

COPY . /app
WORKDIR /app

RUN pip install -e .
