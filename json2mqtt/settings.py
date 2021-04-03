import os

from ruamel import yaml
from ruamel.yaml.composer import ComposerError


SETTINGS_SCHEMA = {
    "schema_dir": {
        "type": str,
        "default": "./schemas",
        "required": True
    },
    "mqtt_host": {
        "type": str,
        "default": "localhost",
        "required": True
    },
    "mqtt_port": {
        "type":  int,
        "default": 1883,
        "required": True
    },
    "mqtt_username": {
        "type": str,
        "default": "",
        "required": False
    },
    "mqtt_password": {
        "type": str,
        "default": "",
        "required": False
    },
    "mqtt_topic": {
        "type": str,
        "default": "home/json2mqtt",
        "required": True
    },
    "mqtt_ssl": {
        "type": bool,
        "default": False,
        "required": False
    },
    "mqtt_cert": {
        "type": str,
        "default": "/etc/ssl/cert.pem",
        "required": False
    },
    "http_host": {
        "type": str,
        "default": "",
        "required": False
    },
    "http_port": {
        "type": int,
        "default": 80,
        "required": False
    }
}


class ConfigError(AssertionError):
    pass


class Singleton(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Settings(object, metaclass=Singleton):
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
        yml.indent(
            mapping=2,
            sequence=4,
            offset=2
        )

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
                if isinstance(value, str):
                    value = value.format(**data)
                setattr(self, key, value)

        return True

    def verify(self):
        for key, cfg in SETTINGS_SCHEMA.items():
            datatype = cfg.get('type')
            default = cfg.get('default')
            required = cfg.get('required')

            value = getattr(self, key, default)

            if required and not value or not isinstance(value, datatype):
                raise ConfigError(f'{key} is required but not found '
                                  f'or incorrect type in {self.filename}')
        return True

    def create(self):
        return self.write(
            data={
                key: SETTINGS_SCHEMA[key]["default"]
                for key in SETTINGS_SCHEMA if SETTINGS_SCHEMA[key]["required"]
            }
        )

    def reload(self):
        self.__init__(filename=self.filename)
