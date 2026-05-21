import json
from pathlib import Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Annotated
from fastapi import Depends, HTTPException, status


DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json_file(filename: str) -> dict | list:
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dks() -> dict | list:
    """Load the datenklos.json file into memory."""
    return _load_json_file("dks.json")


def load_users() -> dict | list:
    """Load the users.json file into memory."""
    return _load_json_file("users.json")


# Initial data load
dks = load_dks()

security = HTTPBasic()
users = load_users()


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
