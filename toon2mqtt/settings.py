import os
from urllib.parse import urljoin

from ruamel import yaml
from ruamel.yaml.composer import ComposerError


SETTINGS_SCHEMA = {
    "mqtt_host": {
        "type": str,
        "default": "localhost",
    },
    "mqtt_port": {
        "type":  int,
        "default": 1883,
    },
    "mqtt_username": {
        "type": str,
        "default": "",
    },
    "mqtt_password": {
        "type": str,
        "default": "",
    },
    "mqtt_topic": {
        "type": str,
        "default": "home/toon2mqtt",
    },
    "mqtt_ssl": {
        "type": bool,
        "default": False,
    },
    "mqtt_cert": {
        "type": str,
        "default": "/etc/ssl/cert.pem",
    },
    "toon_host": {
        "type": str,
        "default": "unset",
    },
    "toon_port": {
        "type": int,
        "default": 80,
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


class BaseClass(object):
    class_name = 'BaseClass'

    def __init__(self, data=None):
        super().__init__()
        self.data = data or {}

    def all(self):
        return self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data.update(
            {key: value}
        )

    def update(self, data):
        self.data.update(
            {key: value for key, value in data}
        )

    def clear(self):
        self.data = dict()

    def __repr__(self):
        return {self.class_name: self.all()}


class Settings(BaseClass, metaclass=Singleton):
    class_name = 'Settings'

    def __init__(self, filename="setting.yaml"):
        self.filename = filename
        self.yaml = self._yaml()

        if not os.path.isfile(filename):
            self.create()

        super().__init__(data=self.read())

        self.parse()
        self.verify()

    @staticmethod
    def _yaml():
        """ Create a ruamel yaml object
            :return: A ruamel yaml object
        """
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
        """ Read a yaml settings file
            :return: a yaml settings object
        """
        with open(self.filename, 'r') as fh:
            content = fh.read()

        try:
            return self.yaml.load(content)
        except ComposerError:
            # For now, get only the first object in the yaml file
            # ignore the following objects
            for item in self.yaml.load_all(content):
                return item

    def write(self, data, overwrite=False):
        """ Write a yaml settings file

        :param data:        The data to write to the file
        :param overwrite:   To overwrite the file or not (defailt: false)
        :return:            None
        """
        if not overwrite and os.path.isfile(self.filename):
            raise FileExistsError(self.filename)

        with open(self.filename, 'w+') as fh:
            self.yaml.dump(data, fh)

    def parse(self):
        for key, value in self.data.items():
            if isinstance(value, str):
                value = value.format(**self.data)
            self.set(key, value)

    def verify(self):
        for key, cfg in SETTINGS_SCHEMA.items():
            datatype = cfg.get('type')
            default = cfg.get('default')

            value = self.get(key, default)

            if key not in self.data or \
                    not isinstance(value, datatype) or \
                    value == "unset":
                raise ConfigError(f'{key} not found or incorrect type in {self.filename}')

    def create(self):
        """ Create a yaml settings file
            :return: None
        """
        self.write(
            data={key: SETTINGS_SCHEMA[key]["default"] for key in SETTINGS_SCHEMA},
            overwrite=False
        )

    def reload(self):
        """ Reload a yaml settings object: reread from file
        """
        self.__init__(filename=self.filename)
