FROM python:3.9-alpine
MAINTAINER Flip Hess <flip@fliphess.com>

COPY . /opt/json2mqtt

RUN true \
 && addgroup --system --gid 1234 json2mqtt \
 && adduser --system -u 1234 --home /opt/json2mqtt --shell /sbin/nologin --ingroup json2mqtt json2mqtt \
 && chown -R json2mqtt:json2mqtt /opt/json2mqtt

USER json2mqtt
WORKDIR /opt/json2mqtt

RUN true \
 && python3 -m venv ./venv \
 && source ./venv/bin/activate \
 && pip --no-cache-dir --disable-pip-version-check --quiet install .

ENTRYPOINT ["./venv/bin/json2mqtt"]


