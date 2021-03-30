# {
#     "mmb":" false",
#     "version": "37"
# }

MODULE_VERSION_SCHEMA = {
    "name": "module_version",
    "endpoint": "/happ_thermstat?action=getModuleVersion",
    "interval": 3600,
    "fields": {
        "mmb": {
            "type": bool,
            "path": "mmb",
        },
        "version": {
            "type": int,
            "path": "version",
        }
    }
}
