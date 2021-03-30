# {
#     "sampleTime": "29-03-2021 19:26:00",
#     "boilerSetpoint": 0,
#     "roomTempSetpoint": 20,
#     "boilerPressure": 0,
#     "roomTemp": 20.65,
#     "boilerOutTemp": null,
#     "boilerInTemp": null,
#     "boilerModulationLevel": 0
# }

BOILERVALUES_SCHEMA = {
    "name": "boilervalues",
    "endpoint": "/boilerstatus/boilervalues.txt",
    "interval": 10,
    "fields": {
        "last_update": {
            "type": str,
            "path": "sampleTime",
        },
        "boiler_setpoint": {
            "type": float,
            "path": "boilerSetpoint",
        },
        "room_temperature_setpoint": {
            "type": int,
            "path": "roomTempSetpoint",
        },
        "boiler_pressure": {
            "type": int,
            "path": "boilerPressure",
        },
        "room_temperature": {
            "type": float,
            "path": "roomTemp",
        },
        "boiler_out_temperature": {
            "type": float,
            "path": "boilerOutTemp",
        },
        "boiler_in_temperature": {
            "type": float,
            "path": "boilerInTemp",
        },
        "boiler_modulation_level": {
            "type": int,
            "path": "boilerModulationLevel",
        }
    }
}
