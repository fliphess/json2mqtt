import glob
import json
import os

from json import JSONDecodeError
from ruamel import yaml
from ruamel.yaml.composer import ComposerError


SETTINGS_SCHEMA = {
    "schema_dir": {
        "type": str,
        "default": "./schemas",
    },
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

    @staticmethod
    def _read(filename):
        with open(filename, 'r') as fh:
            return fh.read()

    def all(self):
        return self.data.items()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data.update(
            {key: value}
        )

    def delete(self, key):
        self.data.pop(key)

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
        content = self._read(filename=self.filename)

        try:
            return self.yaml.load(content)
        except ComposerError:
            # For now, get only the first object in the yaml file
            # ignore the following objects
            for item in self.yaml.load_all(content):
                return item

    def write(self, data):
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
            data={key: SETTINGS_SCHEMA[key]["default"] for key in SETTINGS_SCHEMA}
        )

    def reload(self):
        """ Reload a yaml settings object: reread from file
        """
        self.__init__(filename=self.filename)


class Schemas(BaseClass, metaclass=Singleton):
    class_name = 'Schemas'

    def __init__(self, schema_dir, logger):
        super().__init__(data={})
        self.schema_dir = schema_dir
        self.logger = logger

        self.schema_files = [
            f for f in glob.glob(os.path.join(schema_dir, "*.json"))
            if os.path.isfile(f)
        ]

        self.verify()

    def verify(self):
        if not os.path.isdir(self.schema_dir):
            os.makedirs(self.schema_dir, exist_ok=True)

    def reload(self):
        self.logger.debug(f'Reloading all schemas')
        self.__init__(logger=self.logger, schema_dir=self.schema_dir)

    def add(self, filename):
        schema = self.read(filename=filename)

        if schema:
            name = schema.get('name')
            schema.update({"filename": filename})

            self.logger.debug(f'Adding schema {name}')
            self.set(key=name, value=schema)

    def remove(self, name):
        data = self.get(name, None)
        filename = data.get('filename', None)

        if filename and os.path.isfile(filename):
            self.logger.info(f'Removing schema {name}')
            os.rename(filename, f"{filename}.removed")

    def import_all(self):
        self.logger.debug('Importing all schemas')

        for filename in self.schema_files:
            self.add(filename=filename)

    def dump_all(self):
        self.logger.debug('Dumping all schemas to disk')

        for name, schema in self.all():
            filename = schema.get('filename')

            self.logger.debug(f'Writing schema {name} to {filename}')
            self.write(filename=filename, data=schema)

    def read(self, filename):
        content = self._read(filename=filename)

        try:
            return json.loads(content)
        except JSONDecodeError:
            self.logger.warning(f"Schema {filename} invalid json! Skipping!")

    @staticmethod
    def write(filename, data):
        with open(filename, 'w+', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=4)

