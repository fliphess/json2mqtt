import os
from json import JSONDecodeError

import jmespath
import multitimer
import requests

TYPES = {
    "String": str,
    "Integer": int,
    "Float": float,
    "Boolean": bool,
    "None": None,
    "List": list,
    "Dictionary": dict,
}


class Scheduler(object):
    def __init__(self, client):
        self.client = client
        self.settings = self.client.settings
        self.schemas = self.client.schemas
        self.logger = self.client.logger
        self.timers = {}

    @staticmethod
    def _typematch(instance, stringtype):
        ctype = TYPES.get(stringtype.title(), None)
        return isinstance(instance, ctype)

    def _process(self, data, schema):
        name = schema.get('name')
        url = schema.get('url')

        self.logger.debug(f'Processing data for {name} from {url}')

        for key, cfg in schema.get('fields', {}).items():
            self.logger.debug(f'Parsing field {key}')

            value = jmespath.search(cfg.get('path'), data)

            stringtype = cfg.get('type')
            if value is None or not self._typematch(instance=value, stringtype=stringtype):
                self.logger.debug(f"Incorrect type for {name}: No {stringtype}: Skipping values for {key}={value}")
                continue

            self.logger.debug(f'Sending data for {name}.{key}')
            topic = self.client.topic(name=name, key=key)

            self.client.publish(topic=topic, payload=str(value))

        return True

    def publish(self, name, response):
        for topic, payload in (
                ("request/status_code", response.status_code),
                ("request/reason", response.reason),
                ("request/success", response.ok),
                ("request/url", response.url),
                ("request/elapsed", str(response.elapsed))):
            topic = self.client.topic(name=name, key=topic)

            self.client.publish(topic=topic, payload=payload)

        return True

    # noinspection PyUnboundLocalVariable, PyBroadException
    def fetch(self, *args, **kwargs):
        schema = kwargs.get('schema')
        name = schema.get('name')
        url = schema.get('url')
        timeout = schema.get('timeout', 10)
        headers = {
            key: value for key, value in schema.get('headers', {})
        }

        self.logger.debug(f"Fetching data for {name} from {url}")

        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            self.publish(name=name, response=response)

            response.raise_for_status()
            return self._process(data=response.json(), schema=schema)

        except JSONDecodeError:
            self.logger.error(f'Invalid json for {name} from url: {url}')

        except Exception as e:
            self.logger.error(f'Failed to retrieve for {name}: {url}: {e}')

    def start(self):
        self.logger.info('Starting schema crawlers')
        for name, schema in self.schemas.items():
            if name not in self.timers.keys():
                self.add_timer(name=name)

        return True

    def stop(self):
        self.logger.info('Stopping schema crawlers')

        for name, schema in self.schemas.items():
            self.logger.debug(f'Stopping schema crawlers for {name}')
            self.remove_timer(name=name)

        return True

    def add_timer(self, name):
        schema = self.schemas.get(name, None)
        if not schema:
            return False

        if name not in self.timers:
            interval = schema.get('interval')
            count = schema.get('count', -1)

            self.logger.info(
                f"Starting {name} {'for {} times'.format(count) if count > 0 else 'repeating'} every {interval}s"
            )

            timer = multitimer.MultiTimer(
                interval=interval,
                function=self.fetch,
                kwargs=dict(schema=schema),
                count=count,
            )
            self.timers.update({name: timer})
        else:
            timer = self.timers.get(name)

        timer.start()

        return True

    def remove_timer(self, name):
        self.logger.info(f'Removing schema {name}')

        timer = self.timers.pop(name, None)
        if timer:
            return self.stop_timer(timer=timer)

        return False

    def pause_timer(self, name):
        self.logger.info(f'Pausing schema {name}')

        timer = self.timers.get(name, None)

        if timer:
            return self.stop_timer(timer=timer)

        return False

    @staticmethod
    def start_timer(timer):
        if timer:
            timer.start()

        return True

    @staticmethod
    def stop_timer(timer):
        if timer:
            timer.stop()
            timer.join()

        return True