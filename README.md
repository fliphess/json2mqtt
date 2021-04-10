# Json HTTP to MQTT utility.

Json2mqtt is a little python daemon that retrieves data
from json api's and sends selected fields to an MQTT broker.

It can be used to retrieve data from any http api that returns json.

Write a (bunch of) schema file(s),
feed it to the daemon by files or over mqtt
and every interval you receive the returns on a mqtt topic.

Using the schemas you can give fine-grained instructions to the daemon
which elements you want to publish at which interval


## Timers

For each schema, a new timer is started in its own thread.

They remain in sleep state until the next interval,
and keep doing this until their count value is reached (or indefinitely).

When a timer triggers a new data retrieval,
the requested fields and some metrics about the request
are sent to the mqtt broker.

## Schemas

All schemas, in the `schemas_dir` directory, as configured in `settings.yaml`
are loaded at start-up unless explicitly disabled
setting `"enabled": false` in the schema definition.

There are some predefined schemas that can be used
in the `schemas` directory in this repository,
that you can use to poll a rooted Toon.

A schema is a json definition containing instructions
for the daemon on which fields to publish to MQTT

You can write your own schemas and feed them
to this service as a file or over MQTT.


### Schema required fields

A schema consists of 4 main (required) elements:

- `name`     - The name of the schema
- `url` -    - The url to retrieve json data from

- `interval` - The time in seconds between retrievals

- `fields`   - A list of dictionaries each containing a path and a type element defining fields that
               are to be expected in the retrieved json. (more info below)


### Additional/Optional schema elements

Additional optional elements are:

- `topic`    - Override the topic where to send the data to.
               (The topic is appended with the value of the `name` of the schema)

- `count`    - How many times the crawl should be performed. Default is `-1`,
               which keeps repeating the request until the timer is stopped,
               waiting to be started again

- `timeout`  - The timeout for the http requests (Default is 10s)

- `headers`  - A list of key value pairs with additional headers (can be used for host, auth, user-agent etc)

- `enabled`  - Explicitly enable or disable the schema at startup (The schema needs to exist on disk to be loaded at startup)


### Fields

A `field` element consists of 2 required fields:

- `path`   - The jmespath of the value to send to mqtt
- `type`   - The type of data in this field


Optional fields are:

- `cast`   - Cast the current `type` to another type, useful for "number" or "true" and other returned strings.
             Allowed values are equal to the `type` element, but with a bit of common sense, and a bit of python added.

The types available:

- `String`
- `Integer`
- `Float`
- `Boolean`
- `None`
- `List`
- `Dictionary`


### Schema example

Example: retrieve the module version data from the toon and send over MQTT

```json
{
    "name": "module_version",
    "url": "http:///toon.local/happ_thermstat?action=getModuleVersion",
    "interval": 3600,
    "timeout": 30,
    "headers": [
        {
            "key": "User-Agent",
            "value": "Json2MQTT"
        },
        {
            "key": "Authorization",
            "value": "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
        }
    ],
    "fields": {
        "mmb": {
            "type": "String",
            "cast": "Boolean",
            "path": "mmb"
        },
        "version": {
            "type": "String",
            "path": "version"
        }
    }
}
```

The topics used to publish to in this example are:
- `home/json2mqtt/module_version/mmb`
- `home/json2mqtt/module_version/version`

Or you can override the topics using the `topic` field.


## Install

### Clone the repo

```shell
git clone https://github.com/fliphess/json2mqtt.git && cd json2mqtt
```


### Install in a virtualenv

#### Create venv

Create a virtualenv and install `json2mqtt` and its requirements:

```shell
python3 -m venv venv
source venv/bin/activate

pip install  .
```

#### Create a config

A config file is created on first run if nonexistent:

```shell
json2mqtt --settings settings.yaml --init

vim settings.yaml
```

### Run json2mqtt

```shell
json2mqtt --config settings -vvv
```


## Install using docker

### Build the container:

```shell
docker build -t json2mqtt .
```

### Create a config file

```shell
docker run \
  -ti \
  -v "/tmp:/cfg" \
  --rm json2mqtt \
  --config /cfg/settings.yaml

mv /tmp/settings.yaml .
vim settings.yaml
```

### Run

```shell
docker run \
	--rm \
	-ti \
	-v "$(pwd)/settings.yaml:/opt/json2mqtt/settings.yaml" \
        -v "$(pwd)/schemas:/opt/json2mqtt/schemas" \
	json2mqtt --config settings.yaml -vvv
```


## The `settings.yaml` file

The config file will be created on first run if it does not exist.
It will fill up the required fields with the default values.
This will not suffice to start the daemon, as you need to configure your broker first.

A full configuration file contains:

```yaml
mqtt_host: "some.broker"
mqtt_port: 1883

mqtt_username: "username"
mqtt_password: "password"

mqtt_topic: home/toon2mqtt

mqtt_ssl: true
mqtt_cert: "/etc/ssl/cert.pem"

schema_dir: ./schemas
```


## Controlling the daemon

You can control the daemon over MQTT.

You can start and stop timers, add, remove and reload schemas.


## MQTT Topics:

### Publishing topics:

The topics to which the retrieved data and response metrics are send:
```
home/json2mqtt/<schema name>/<key>               # Retrieved json keys from api
home/json2mqtt/<schema name>/request/success     # If the last request succeeded
home/json2mqtt/<schema name>/request/status_code # The status code of the last request
home/json2mqtt/<schema name>/request/reason      # The reason of the last request
home/json2mqtt/<schema name>/request/url         # The full url of the request
```

### Command topics

The topics to publish to, to create, list and manipulate the schemas

```
home/json2mqtt/command/schema/add                # Add a json schema from the mqtt payload
                                                 # Input: a json schema

home/json2mqtt/command/schema/add_file           # Add a json schema from a file that is present on disk
                                                 # Input: a filename of a file in the schema_dir

home/json2mqtt/command/schema/remove             # Remove/Disable a schema
                                                 # Input: the name of the schema to remove (See: `schema/list`)

home/json2mqtt/command/schema/list               # List all json schemas
                                                 # No input required, an empty string or a 0 suffices.

home/json2mqtt/command/schema/import             # Import all schemas from disk
                                                 # No input required, an empty string or a 0 suffices.

home/json2mqtt/command/schema/dump               # Write all schemas to disk
                                                 # No input required, an empty string or a 0 suffices.
```

Schemas can be manipulated, loaded and written to disk.
They are used by the scheduler, but not automatically renewed.
To update the timers that use the schemas, you additionally need to reload the scheduler task(s)

### Timer topics


Timers can be controlled separately from the schemas that are used to instruct what to crawl and how often.
```
home/json2mqtt/command/scheduler/list            # List all timers
                                                 # No input required, an empty string or a 0 suffices.

home/json2mqtt/command/scheduler/stop            # Stop all timers
                                                 # No input required, an empty string or a 0 suffices.

home/json2mqtt/command/scheduler/start           # Start all (not running) timers
                                                 # No input required, an empty string or a 0 suffices.

home/json2mqtt/command/scheduler/add_timer       # Add a timer using a json schema, do not save anything to schemas, 
                                                 # just start the timer (single use, will be gone after a restart)

home/json2mqtt/command/scheduler/remove_timer    # Remove a timer
home/json2mqtt/command/scheduler/start_timer     # Start a stopped timer
home/json2mqtt/command/scheduler/pause_timer     # Stop a running timer
```

All commands return their output to `home/json2mqtt/talkback`


## Known issues

### Casting to bool

Casting string "1" and "0" values to a boolean is tricky:

```
In [1]: bool("0")
Out[1]: True
```

Instead, don't do a cast at all and use  the `1` and `0` strings directly.

### Dotted fields

Due to the way [jmespath for python](https://pypi.org/project/jmespath/) works, keys containing a dot,
need to be contained by escaped double quotes:

```
{
  "fields": {
      "electricity_delivered_lt_flow": {
        "type": "String",
        "path": "\"dev_2.6\".CurrentElectricityFlow"
      },
  }
}
```
