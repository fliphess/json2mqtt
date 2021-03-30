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

    def url(self, endpoint):
        host = self.settings.get('toon_host')
        port = self.settings.get('toon_port')

        return urljoin(
            base=f"http://{host}:{port}",
            url=endpoint
        )

    def fetch(self, *args, **kwargs):
        url = kwargs.get('url')
        schema = kwargs.get('schema')

        self.logger.debug(f"Fetching data for {schema.get('name')}"
                          f" on {schema.get('endpoint')}")

        response = requests.get(url, timeout=5)

        try:
            response.raise_for_status()
            self.process(data=response.json(), schema=schema)
        except HTTPError:
            self.logger.error(f'Failed to retrieve: {url}: {response.status_code} {response.reason}')

    def process(self, data, schema):
        name = schema.get('name')
        endpoint = schema.get('endpoint')

        self.logger.debug(f'Processing data for {name}: {endpoint}')

        for key, cfg in schema.get('fields', {}).items():
            self.logger.debug(f'Parsing field {key}')

            value = jmespath.search(cfg.get('path'), data)

            if value is None or not isinstance(value, cfg.get('type')):
                self.logger.debug(f"Incorrect type: Skipping values for {key}={value}")
                continue

            self.logger.debug(f'Sending data for {name}.{key}')
            topic = self.client.topic(name=name, key=key)
            self.client.publish(topic=topic, payload=value)

    def start(self):
        self.logger.info('Starting schema crawlers')

        for schema in self.schemas:
            name = schema.get('name')
            endpoint = schema.get('endpoint')
            interval = schema.get('interval')

            self.logger.info(f'Starting schema crawler {name} for {endpoint} every {interval}s')

            url = self.url(endpoint=endpoint)

            timer = multitimer.MultiTimer(
                interval=interval,
                function=self.fetch,
                kwargs=dict(url=url, schema=schema),
                count=-1,
            )
            timer.start()

            self.timers.update({schema.get('name'): timer})

    def stop(self):
        self.logger.info('Stopping schema crawlers')

        for schema in self.schemas:
            name = schema.get('name')
            timer = self.timers.get(name, None)
            if timer:
                timer.stop()
                timer.join()
