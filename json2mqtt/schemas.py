import glob
import json
import os

from json import JSONDecodeError
from jsonschema import validate, SchemaError, ValidationError
from json2mqtt.scheduler import TYPES


KEYS_PATTERN = f"^({'|'.join(TYPES.keys())})$"

JSONSCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "url": {
            "type": "string",
            "format": "uri"
        },
        "interval": {
            "type": "number"
        },
        "count": {
            "type": "number"
        },
        "timeout": {
            "type": "number"
        },
        "topic": {
            "type": "string",
        },
        "enabled": {
          "type": "boolean"
        },
        "headers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string"
                    },
                    "value": {
                        "type": "string"
                    }
                }
            }
        },
        "fields": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string"
                },
                "cast": {
                    "type": "string",
                    "pattern": KEYS_PATTERN,
                },
                "type": {
                    "type": "string",
                    "pattern": KEYS_PATTERN,
                }
            }
        }
    },
    "required": [
        "name",
        "url",
        "interval",
        "fields",
    ]
}


class Schemas(dict):
    def __init__(self, logger, schema_dir="./schemas"):
        super().__init__()
        self.schema_dir = schema_dir
        self.logger = logger

        self.schema_files = [
            f for f in glob.glob(os.path.join(self.schema_dir, "*.json"))
            if os.path.isfile(f)
        ]
        self.verify()

    def verify(self):
        if not os.path.isdir(self.schema_dir):
            os.makedirs(self.schema_dir, exist_ok=True)

    def reload(self):
        self.logger.debug('Reloading all schemas')
        self.__init__(logger=self.logger)

    def add_schema_file(self, filename):
        schema = self.read(filename=filename)

        if not schema:
            self.logger.warning(f'Invalid schema file in {filename}')
            return False

        if filename not in self.schema_files:
            self.schema_files.append(filename)

        schema.update({"filename": filename})

        self.add_schema(schema=schema)

        return True

    def add_schema(self, schema):
        try:
            validate(instance=schema, schema=JSONSCHEMA)
        except (SchemaError, ValidationError):
            return False

        name = schema.get('name')
        enabled = schema.get('enabled', True)

        if enabled is False:
            self.logger.warning(f'Schema file {name} is disabled')
            return False

        self.logger.debug(f'Adding schema {name}')
        self.update({name: schema})

    def remove_schema(self, name):
        schema = self.get(name, None)

        if not schema:
            return False

        self.logger.info(f'Removing schema {name}')
        self.pop(name)

        filename = schema.get('filename', None)
        if filename and os.path.isfile(filename):
            os.rename(filename, f"{filename}.removed")

            if filename in self.schema_files:
                self.schema_files.remove(filename)

        return True

    def import_all(self):
        self.logger.debug('Importing all schemas')
        for filename in self.schema_files:
            self.add_schema_file(filename=filename)

        return True

    def dump_all(self):
        self.logger.debug('Dumping all schemas to disk')

        for name, schema in self.items():
            filename = schema.pop('filename')
            self.logger.debug(f'Writing schema {name} to {filename}')
            self.write(filename=filename, data=schema)

        return True

    def read(self, filename):
        with open(filename, 'r') as fh:
            return self.load(content=fh.read())

    @staticmethod
    def write(filename, data):
        with open(filename, 'w+', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=4)

        return True

    @staticmethod
    def load(content):
        try:
            return json.loads(content)
        except JSONDecodeError:
            pass
