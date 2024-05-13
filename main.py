import json
import re
from math import e
from operator import contains
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ValidationError

from msisdn import generate_default_msisdn, get_msisdn_by_imsi, set_default_msisdn, set_msisdn_by_imsi
from osmo import (
    OsmocomHLR,
    OsmocomMSC,
    osmo_hlr_run_multiple,
    osmo_hlr_run_multiple_elevated,
    osmo_hlr_run_single,
    osmo_hlr_run_single_elevated,
    osmo_msc_run_multiple,
    osmo_msc_run_multiple_elevated,
    osmo_msc_run_single,
    osmo_msc_run_single_elevated,
)

security = HTTPBasic()

app = FastAPI(
    dependencies=[Depends(security)],
    title="EMF GSM API",
    description="A simple API for managing GSM services at EMF Camp.",
    contact={"name": "EMF GSM Team", "url": "https://gsm.emf.camp/", "email": "poc+gsmapi@emfcamp.org"},
    version="0.0.1",
    terms_of_service="https://gsm.emf.camp/api/tos",
    license_info={"name": "Beerware", "url": "https://spdx.org/licenses/Beerware.html"},
)


def load_dks():
    """Load the datenklos.json file into memory."""
    with open("dks.json", "r") as f:
        return json.load(f)


dks = load_dks()


def load_users():
    """Load the users.json file into memory."""
    with open("users.json", "r") as f:
        return json.load(f)


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


class MSISDNResponse(BaseModel):
    imsi: int = 999430000001234
    msisdn: int = 4242


@app.get("/", include_in_schema=False)
async def read_root():
    """Redirect root to the EMF GSM page."""
    return RedirectResponse(url="https://gsm.emf.camp/")


@app.get(
    "/imsi/{imsi}/get/current",
    summary="Get Current MSISDN",
    responses={
        200: {
            "description": "Current MSISDN found successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        404: {
            "description": "Subscriber not found.",
            "content": {"application/json": {"example": {"detail": "Subscriber not found."}}},
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {"application/json": {"example": {"detail": "An unhandled error occurred."}}},
        },
    },
    response_model=MSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def get_current(imsi: int, verified: bool = Depends(verification)):
    """Grab the Current MSISDN for a given IMSI"""
    try:
        return get_msisdn_by_imsi(imsi)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.post(
    "/imsi/{imsi}/set/new/{new_msisdn}",
    summary="Set New MSISDN",
    responses={
        200: {
            "description": "Set MSISDN successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "Number already in use. Please try a different number.",
            "content": {"application/json": {"example": {"detail": "Number already in use. Please try a different number."}}},
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
    response_model=MSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def set_new_msisdn(imsi: int, new_msisdn: int, verified: bool = Depends(verification)):
    """Set a new MSISDN for a given IMSI"""
    try:
        return set_msisdn_by_imsi(imsi, new_msisdn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Number already in use. Please try a different number.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.post(
    "/imsi/{imsi}/set/reset/{type}/{prefix}",
    summary="Set Default MSISDN",
    responses={
        200: {
            "description": "Set MSISDN successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "Number already in use.",
            "content": {"application/json": {"example": {"detail": "Number already in use. Please try a different number."}}},
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
    response_model=MSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def set_default(imsi: int, type: int, prefix: int, verified: bool = Depends(verification)):
    """Set the Default MSISDN for a given IMSI"""
    try:
        return set_default_msisdn(imsi, type, prefix)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Number already in use. Please try a different number.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/imsi/{imsi}/get/default/{type}/{prefix}",
    summary="Get Default MSISDN",
    responses={
        200: {
            "description": "Default MSISDN generated successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
    response_model=MSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def get_default(imsi: int, type: int, prefix: int, verified: bool = Depends(verification)):
    """Get the Default MSISDN for a given IMSI"""
    try:
        return {"imsi": imsi, "msisdn": generate_default_msisdn(imsi, type, prefix)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


class GetLocationResponse(BaseModel):
    imsi: int = 999430000001234
    lac: int = 12345
    cell_id: int = 1800
    dk: str = "C4"


@app.get(
    "/imsi/{imsi}/get/location",
    summary="Get Location Information",
    tags=["IMSI Driven Operations"],
    responses={
        200: {
            "description": "Location information found successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "lac": 12345, "cell_id": 1800, "dk": "C4"}}},
        },
        404: {
            "description": "Subscriber not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Subscriber 999430000001234 not found on the network, Please ensure the device is turned on, and that you have used the correct IMSI. If this error persists, please contact the EMF POC/GSM team."
                    }
                }
            },
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
    response_model=GetLocationResponse,
)  # Add closing curly brace here
async def get_location(imsi: int, verified: bool = Depends(verification)):
    """Get the Location Information for a given IMSI

    This will return the LAC / cell ID for the given IMSI, which can be used to determine the location of the device.
    """
    try:
        raw = osmo_msc_run_single(f"show subscriber imsi {imsi}")
        lines = raw.splitlines()
        print(lines)
        for line in lines:
            if f"% No subscriber found for imsi {imsi}" in line:
                print("hit")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Subscriber {imsi} not found on the network, Please ensure the device is turned on, and that you have used the correct IMSI. If this error persists, please contact the EMF POC/GSM team.",
                )
            if re.match(r"^\s*LAC / cell ID:", line):
                lac, cell_id = line.strip().replace("LAC / cell ID: ", "").strip().split(" / ")
                return {
                    "imsi": imsi,
                    "lac": int(lac),
                    "cell_id": int(cell_id),
                    "dk": (dks[lac] if lac in dks.keys() else None),
                }
    except HTTPException as e:
        raise (e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.post(
    "/sim/create/{imsi}/{type}/{prefix}/{ki}/{opc}",
    summary="Create SIM in HLR",
    tags=["SIM Operations"],
    responses={
        200: {
            "description": "SIM created successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
)
async def set_create_sim(imsi: int, type: int, prefix: int, ki: str, opc: str, verified: bool = Depends(verification)):
    """Creates a New SIM entry in the HLR"""
    try:
        osmo_hlr_run_multiple_elevated(
            [
                f"subscriber imsi {imsi} create",
                f"subscriber imsi {imsi} update msisdn {generate_default_msisdn(imsi, type, prefix)}",
                f"subscriber imsi {imsi} update network-access-mode cs+ps",
                f"subscriber imsi {imsi} update aud3g milenage k {ki} opc {opc}",
            ]
        )
        return {"imsi": imsi, "msisdn": generate_default_msisdn(imsi, type, prefix)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}",
        )


@app.get(
    "/msisdn/{msisdn}/imsi",
    summary="Get IMSI from HLR by Assigned MSISDN",
    tags=["MSISDN Driven Operations"],
    responses={
        200: {
            "description": "IMSI found successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        404: {
            "description": "MSISDN not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "MSISDN 4242 not found in the HLR, please ensure you have entered the correct MSISDN. If this error persists, please contact the EMF POC/GSM team."
                    }
                },
            },
        },
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {"example": {"detail": "An unhandled error occurred. Error: Something went wrong."}}
            },
        },
    },
)
async def get_imsi_by_msisdn(msisdn: int, verified: bool = Depends(verification)):
    """Get the IMSI for a given MSISDN"""
    try:
        raw = osmo_hlr_run_single(f"show subscriber msisdn {msisdn}")
        print(raw)
        lines = raw.splitlines()
        for line in lines:
            if line.strip().startswith("IMSI: "):
                return {"imsi": int(line.split(":")[1].strip()), "msisdn": msisdn}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MSISDN {msisdn} not found in the HLR, please ensure you have entered the correct MSISDN. If this error persists, please contact the EMF POC/GSM team.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
