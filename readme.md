# OSMOAPI
FastAPI based wrapper for various osmocom interfaces

## Configs
`dks.json` contains the LAC to DK relationship, this is used as part of the Location Request flow 
```json
{
    "12345": "A1",
    "54321": "B2",
    ...
}
```

`users.json` contains user credentials for HTTP Basic Auth. This is intentionally the bare-minimum, as this API should be ran internally at the Event network within a closed network.
```json
{
    "emfpoc": {
        "password": "herebedragons"
    },
    ...
}
```

## Run

`fastapi dev --host 0.0.0.0` for development - this enables Live Updating
`fastapi run` to run in "Production"