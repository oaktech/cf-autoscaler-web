FROM alpine

ENV DEVDEPS "gcc musl-dev python-dev make openssl-dev py2-pip"

ADD . /app

WORKDIR /app

EXPOSE 5000

RUN apk update && apk add $DEVDEPS python && \
    pip install -r /app/requirements.txt && \
    apk del $DEVDEPS

ENTRYPOINT python server.py
