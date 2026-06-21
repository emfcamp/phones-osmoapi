# OSMOAPI
FastAPI based wrapper for various osmocom interfaces

## Installation

Install uv: https://docs.astral.sh/uv/getting-started/installation/

Makes use of osmoapi from here: https://github.com/emfcamp/phones-osmoapi-py/releases/

## Configs
`app/data/dks.json` contains the LAC to DK relationship, this is used as part of the Location Request flow
```json
{
    "1": {
        "name": "Stage E",
        "type": "gsm",
        "lat": 52.1392069,
        "lon": -2.1793473
    },
    ...
}
```

`app/data/users.json` contains user credentials for HTTP Basic Auth. This is intentionally the bare-minimum, as this API should be ran internally at the Event network within a closed network.
```json
{
    "emfpoc": {
        "password": "herebedragons"
    },
    ...
}
```

`app/data/tokens.json` contains HTTP bearer tokens for interactions with core and other services.
```json
{
    "core": "I0qvYe73uLtqwCQqXgBqqJpQobGEq988"
    ...
}
```

## Data files
`app/data/default_msisdn_by_imsi.csv` should contain a mapping from IMSI to DefaultMSISDN; for example:
```csv
IMSI,DefaultMSISDN
999430000001234,90424242
```

## Run

`uv run fastapi dev --host 0.0.0.0` for development - this enables Live Updating
`uv run fastapi run` to run in "Production"


## Run (Docker)

`docker compose --profile prod up --force-recreate` - for prod profile

`docker compose --profile dev up --force-recreate` - for dev profile
