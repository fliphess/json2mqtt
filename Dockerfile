FROM python:3.9-alpine
MAINTAINER Flip Hess <flip@fliphess.com>

COPY . /opt/toon2mqtt

RUN true \
 && addgroup --system --gid 1234 toon2mqtt \
 && adduser --system -u 1234 --home /opt/toon2mqtt --shell /sbin/nologin --ingroup toon2mqtt toon2mqtt \
 && chown -R toon2mqtt:toon2mqtt /opt/toon2mqtt

USER toon2mqtt
WORKDIR /opt/toon2mqtt

RUN true \
 && python3 -m venv ./venv \
 && source ./venv/bin/activate \
 && pip --no-cache-dir --disable-pip-version-check --quiet install .

ENTRYPOINT ["./venv/bin/toon2mqtt"]


