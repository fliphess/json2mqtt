# Toon2mqtt

Toon2mqtt is a little webcrawler that crawls the integration endpoints of a rooted toon and sends the values to a MQTT broker.

I use it to show data from my rooted toon in home-assistant.

It starts a bunch of timers that crawl several endpoints on the toon local device.


## Setup

### Clone the repo

```
git clone https://github.com/fliphess/toon2mqtt.git && cd toon2mqtt
```

### Install

#### Install in a virtualenv

Create a virtualenv and install `toon2mqtt` and its requirements:

```
python3 -m venv venv
source venv/bin/activate

pip install .
```

Create a config file (created if nonexistent):

```
toon2mqtt --settings settings.yaml

vim settings.yaml
```

#### Install using docker

Build the container:

```
docker build -t toon2mqtt .
```

Create a config file (created if nonexistent):

```
docker run -ti -v "/tmp:/cfg" --rm toon2mqtt  --config /cfg/settings.yaml


mv /tmp/settings.yaml .
vim settings.yaml
```


## Running

### In a virtualenv

```
toon2mqtt --config settings -vvv
```

### In a container

```
docker run \
	--rm \
	-ti \
	-v "$(pwd)/settings.yaml:/opt/toon2mqtt/settings.yaml"
	toon2mqtt --config settings.yaml -vvv
```


## Home Assistant Addon

TODO



## Schemas

Schemas are json definitions that can be used to validate
the json data returned from toon (or any other json api).

There are some predefined json schemas that can be used
by enabling them in the `settings.yaml`.

Additionally, you can write your own schemas and feed them
to this service as a file or over MQTT.

A schema consists of 4 main elements:

- name     - The name of the schema
- endpoint - The api endpoint to retrieve json data from (IE: `/some/endpoint` )
- interval - The time in seconds between retrievals
- fields   - A list of dictionaries defining fields that
             are to be expected in the retrieved json.

Optional elements are:

- topic - Override the topic where to send the data to.
          (The topic is appended with the value of the  `name` element)
- host  - The host of the http api to connect to.
- port  - The port of the http api to connect to (set `ssl: true` to enable ssl)
- ssl   - Use ssl for this connection

A `field` element consists of 2 fields:

- path   - The jmespath of the value to send to mqtt
- type   - The type of data in this field

The types available:
- String
- Integer
- Float
- Boolean
- None
- List
- Dictionary


Example: retrieve the module version data from the toon and send over MQTT
```
{
    "name": "module_version",
    "endpoint": "/happ_thermstat?action=getModuleVersion",
    "interval": 3600,
    "fields": {
        "mmb": {
            "type": "Boolean",
            "path": "mmb"
        },
        "version": {
            "type": "Integer",
            "path": "version"
        }
    }
}
```


The topics used to publish to in this example are:
- `home/toon2mqtt/module_version/mmb`
- `home/toon2mqtt/module_version/version`

Or you can override the topics using the `topic` field.

