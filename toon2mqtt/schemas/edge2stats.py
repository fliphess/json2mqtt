# {
#     "last": 67,
#     "shortest": 60,
#     "longest": 48243,
#     "average": 74.606949,
#     "txAckedAfterTries": [11308,0,0],
#     "txNacked": 1,
#     "txTimedOut": 0,
#     "pkgsLost": 0,
#     "rxAcked": 11308,
#     "rxNacked": 0,
#     "_": "_"
# }

EDGE_2_STATS_SCHEMA = {
    "name": "edge2stats",
    "endpoint": "/happ_thermstat?action=getEdge2Stats",
    "interval": 3600,
    "fields": {
        "last": {
            "type": int,
            "path": "last",
        },
        "shortest": {
            "type": int,
            "path": "shortest",
        },
        "longest": {
            "type": int,
            "path": "longest",
        },
        "average": {
            "type": float,
            "path": "average",
        },
        "tx_acked_after_tries": {
            "type": list,
            "path": "txAckedAfterTries",
        },
        "tx_nacked": {
            "type": int,
            "path": "txNacked",
        },
        "tx_timed_out": {
            "type": int,
            "path": "txTimedOut",
        },
        "pkgs_lost": {
            "type": int,
            "path": "pkgsLost",
        },
        "rx_acked": {
            "type": int,
            "path": "rxAcked",
        },
        "rx_nacked": {
            "type": int,
            "path": "rxNacked",
        }
    }
}
