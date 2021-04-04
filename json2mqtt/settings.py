import os

from ruamel import yaml
from ruamel.yaml.composer import ComposerError


class ConfigError(AssertionError):
    pass


class Settings(object):
    schema = {
        "schema_dir": "./schemas",
        "mqtt_host": "localhost",
        "mqtt_port": 1883,
        "mqtt_username": "",
        "mqtt_password": "",
        "mqtt_topic": "home/json2mqtt",
        "mqtt_ssl": False,
        "mqtt_cert": "/etc/ssl/cert.pem",
    }

    __slots__ = [
        'filename',
        'yaml',
        'schema_dir',
        'mqtt_host',
        'mqtt_port',
        'mqtt_username',
        'mqtt_password',
        'mqtt_topic',
        'mqtt_ssl',
        'mqtt_cert'
    ]

    def __init__(self, filename="setting.yaml"):
        self.filename = filename
        self.yaml = self._yaml()

        if not os.path.isfile(filename):
            self.create()

        self.parse()
        self.verify()

    @staticmethod
    def _yaml():
        yml = yaml.YAML()
        yml.preserve_quotes = True
        yml.explicit_start = True
        yml.explicit_end = True
        yml.indent(mapping=2, sequence=4, offset=2)

        return yml

    def read(self):
        with open(self.filename, 'r') as fh:
            content = fh.read()

        try:
            return self.yaml.load(content)
        except ComposerError:
            for item in self.yaml.load_all(content):
                return item

    def write(self, data):
        with open(self.filename, 'w+') as fh:
            self.yaml.dump(data, fh)
        return True

    def parse(self):
        data = self.read()

        for key, value in data.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        return True

    def verify(self):
        for key, default_value in self.schema.items():
            value = getattr(self, key, default_value)

            if value is None or not hasattr(self, key):
                raise ConfigError(f'{key} is required but not found in {self.filename}')

        return True

    def create(self):
        return self.write(
            data={key: value for key, value in self.schema}
        )

    def reload(self):
        self.__init__(filename=self.filename)
