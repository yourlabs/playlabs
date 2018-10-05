FROM alpine:edge

ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1
ENV PATH="${PATH}:/app/.local/bin" HOME="/app"

RUN apk update && apk --no-cache upgrade && apk add --no-cache git bash openssh-client py3-setuptools ansible sshpass && rm -rf /var/cache/apk/* && pip3 install --no-cache-dir -U pip

RUN adduser -u 1000 -h /app -D app
WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip3 install --no-cache -r /app/requirements.txt
ADD . /app
RUN pip3 install --no-cache --no-deps --editable /app

USER app
CMD playlabs
