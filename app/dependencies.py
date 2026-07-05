from .config import settings
from .osmoctrl import OsmoBSC, OsmoHLR, OsmoMSC

import json
from pathlib import Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from fastapi import Depends, HTTPException, status


DATA_DIR = Path(settings.data_dir).resolve().parent / "data"


def _load_json_file(filename: str) -> dict | list:
    file_path = DATA_DIR / filename
    if not file_path.exists():
        print(f"File {file_path} does not exist! Returning empty dict")
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dks() -> dict | list:
    return _load_json_file("dks.json")


def load_users() -> dict | list:
    return _load_json_file("users.json")


def load_tokens() -> dict | list:
    return _load_json_file("tokens.json")


security = HTTPBasic()
bearer_scheme = HTTPBearer()

# App data
tokens = load_tokens()
users = load_users()
dks = load_dks()


def verification(creds: Annotated[HTTPBasicCredentials, Depends(security)]):
    """Verify the user's credentials against the users.json file."""
    username = creds.username
    password = creds.password
    if username in users and password == users[username]["password"]:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password. Please speak to the EMF POC/GSM team if you need access to this service.",
            headers={"WWW-Authenticate": "Basic"},
        )


def make_bearer_verifier(token_key: str):
    async def verify(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> None:
        if credentials.scheme != "Bearer" or credentials.credentials != tokens.get(token_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return verify


def hlr_register_emf_numbers():
    print("Checking hlr for system number")
    subscriber = hlr_instance.get_subscriber_by_msisdn(settings.gsm_system_number)
    if not subscriber:
        hlr_instance.easy_create(
            imsi=settings.gsm_system_imsi,
            msisdn=settings.gsm_system_number,
            cs=False,
            ps=False,
        )
        print(f"Created GSM user with number: {settings.gsm_system_number}")


verify_core_token = make_bearer_verifier("core")
verify_metrics_token = make_bearer_verifier("metrics")


## Osmocom shared instances
bsc_instance = OsmoBSC()
hlr_instance = OsmoHLR()
msc_instance = OsmoHLR()

hlr_register_emf_numbers()
