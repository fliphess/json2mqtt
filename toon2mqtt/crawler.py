from json import JSONDecodeError
from socket import timeout
from urllib.parse import urljoin

import jmespath
import multitimer
import requests
from requests import HTTPError


class Scheduler(object):
    def __init__(self, client):
        self.client = client
        self.settings = self.client.settings
        self.schemas = self.client.schemas
        self.logger = self.client.logger
        self.timers = {}

    @staticmethod
    def _typematch(instance, stringtype):
        ctype = {
            "String": str,
            "Integer": int,
            "Float": float,
            "Boolean": bool,
            "None": None,
            "List": list,
            "Dictionary": dict,
        }.get(stringtype.title(), None)

        return isinstance(instance, ctype)

    def _url(self, endpoint, host=None, port=None, use_ssl=False):
        host = host or self.settings.get('toon_host')
        port = port or self.settings.get('toon_port')
        scheme = "https" if use_ssl else "http"

        return urljoin(
            base=f"{scheme}://{host}:{port}",
            url=endpoint
        )

    def _process(self, data, schema):
        name = schema.get('name')
        endpoint = schema.get('endpoint')

        self.logger.debug(f'Processing data for {name}: {endpoint}')

        for key, cfg in schema.get('fields', {}).items():
            self.logger.debug(f'Parsing field {key}')

            value = jmespath.search(cfg.get('path'), data)

            stringtype = cfg.get('type')
            if value is None or not self._typematch(instance=value, stringtype=stringtype):
                self.logger.debug(f"Incorrect type: not a {stringtype}: Skipping values for {key}={value}")
                continue

            self.logger.debug(f'Sending data for {name}.{key}')
            topic = self.client.topic(name=name, key=key)

            self.client.publish(topic=topic, payload=str(value))

    def publish(self, name, response):
        for topic, payload in (
                ("request/success", response.status_code),
                ("request/status_code", response.ok),
                ("request/reason", response.reason),
                ("request/url", response.url)):
            topic = self.client.topic(name=name, key=topic)
            self.client.publish(topic=topic, payload=payload)

    # noinspection PyUnboundLocalVariable
    def fetch(self, *args, **kwargs):
        url = kwargs.get('url')
        schema = kwargs.get('schema')
        name = schema.get('name')
        endpoint = schema.get('endpoint')

        self.logger.debug(f"Fetching data for {name} on {endpoint}")

        try:
            response = requests.get(url, timeout=10)

            self.publish(name=name, response=response)

            response.raise_for_status()

            self._process(data=response.json(), schema=schema)

        except JSONDecodeError:
            self.logger.error(f'Invalid json from endpoint: {url}')

        except (timeout, HTTPError):
            self.logger.error(f'Failed to retrieve: {url}: {response.status_code} {response.reason}')

    def start(self):
        self.logger.info('Starting schema crawlers')

        for name, schema in self.schemas.all():
            self.add_timer(schema=schema)

    def stop(self):
        self.logger.info('Stopping schema crawlers')

        for name, schema in self.schemas.all():
            self.logger.debug(f'Stopping schema crawlers for {name}')
            self.remove_timer(schema=schema)

    def add_timer(self, schema):
        name = schema.get('name')
        endpoint = schema.get('endpoint')
        interval = schema.get('interval')

        host = schema.get('host', None)
        port = schema.get('port', None)
        use_ssl = schema.get('use_ssl', False)

        url = self._url(endpoint=endpoint, host=host, port=port, use_ssl=use_ssl)

        self.logger.info(f'Starting schema crawler {name} for {url} every {interval}s')

        timer = multitimer.MultiTimer(
            interval=interval,
            function=self.fetch,
            kwargs=dict(url=url, schema=schema),
            count=-1,
        )
        timer.start()

        self.timers.update({schema.get('name'): timer})

    def remove_timer(self, schema):
        name = schema.get('name')
        timer = self.timers.pop(name, None)
        self.stop_timer(name=name, timer=timer)

    def restart_timer(self, name, timer):
        self.logger.info(f'Starting schema {name}')
        timer = self.timers.pop(name, None)
        if timer:
            timer.start()

    def stop_timer(self, name, timer):
        self.logger.info(f'Stopping schema {name}')

        if timer:
            timer.stop()
            timer.join()
