FROM alpine:edge

ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1
ENV PATH="${PATH}:/app/.local/bin"

RUN apk update && apk --no-cache upgrade && apk add --no-cache openssh-client py3-setuptools ansible sshpass && rm -rf /var/cache/apk/* && pip3 install -U pip

RUN adduser -h /app -D app
WORKDIR /app
USER app
CMD playlabs

ADD --chown=app:app requirements.txt /app/requirements.txt
RUN pip3 install --user -r /app/requirements.txt
ADD --chown=app:app . /app
RUN pip3 install --user --no-deps -e /app
