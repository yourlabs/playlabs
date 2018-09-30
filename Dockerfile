FROM alpine:edge

ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1
ENV PATH="${PATH}:/app/.local/bin" HOME="/app"

RUN apk update && apk --no-cache upgrade && apk add --no-cache bash openssh-client py3-setuptools ansible sshpass && rm -rf /var/cache/apk/* && pip3 install --no-cache-dir -U pip

RUN adduser -u 1000 -h /app -D app
WORKDIR /app
USER app
CMD playlabs

ADD --chown=app:app requirements.txt /app/requirements.txt
RUN pip3 install --no-cache --user -r /app/requirements.txt
ADD --chown=app:app . /app
RUN pip3 install --no-cache --user --no-deps -e /app
