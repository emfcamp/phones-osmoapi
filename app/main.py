import json
import re
from operator import contains
from pathlib import Path
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ValidationError

from msisdn import (
    get_all_default_msisdn,
    get_all_msisdn_from_hlr,
    get_msisdn_by_imsi,
    get_default_msisdn_by_imsi,
    reset_msisdn_by_imsi_to_default,
    set_msisdn_by_imsi,
)
from osmoctrl import OsmoBSC, OsmoHLR, OsmoMSC, OsmoSubscriberParam
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
    version="0.1.0",
    terms_of_service="https://gsm.emf.camp/api/tos",
    license_info={"name": "Beerware", "url": "https://spdx.org/licenses/Beerware.html"},
)


DEFAULT_500 = {
    "description": "An unhandled error occurred.",
    "content": {
        "application/json": {
            "example": {
                "detail": "An unhandled error occurred. Error: Something went wrong.",
            }
        }
    },
}


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
users = load_users()

hlr_instance = OsmoHLR()
msc_instance = OsmoMSC()
bsc_instance = OsmoBSC()


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


class DefaultMSISDNResponse(BaseModel):
    imsi: int = 999430000001234
    default_msisdn: int = 4242


class AllMSISDNResponse(BaseModel):
    msisdns: list[int] = [4242, 4243, 4244]


class AllDefaultMSISDNResponse(BaseModel):
    default_msisdns: list[int] = [4242, 4243, 4244]


@app.get("/", include_in_schema=False)
async def read_root():
    """Redirect root to the EMF GSM page."""
    return RedirectResponse(url="https://gsm.emf.camp/")


@app.get(
    "/get_all_default_msisdns",
    summary="Get All Default MSISDNs for Known IMSIs",
    responses={
        200: {
            "description": "Default MSISDNs retrieved successfully.",
            "content": {"application/json": {"example": {"default_msisdns": [4242, 4243, 4244]}}},
        },
        500: DEFAULT_500,
    },
    response_model=AllDefaultMSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def get_all_default_msisdns(verified: bool = Depends(verification)):
    """Get all Default MSISDNs"""
    try:
        msisdns = get_all_default_msisdn()
        return {"default_msisdns": [row["default_msisdn"] for row in msisdns]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/get_all_hlr_msisdns",
    summary="Get All MSISDNs known to the HLR",
    responses={
        200: {
            "description": "HLR MSISDNs retrieved successfully.",
            "content": {"application/json": {"example": {"msisdns": [4242, 4243, 4244]}}},
        },
        500: DEFAULT_500,
    },
    response_model=AllMSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def get_all_hlr_msisdns(verified: bool = Depends(verification)):
    """Get all MSISDNs known to HLR"""
    try:
        msisdns = get_all_msisdn_from_hlr()
        return {"msisdns": [row["msisdn"] for row in msisdns]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


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
        500: DEFAULT_500,
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
        500: DEFAULT_500,
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
    "/imsi/{imsi}/set/reset_msisdn",
    summary="Reset MSISDN to default",
    responses={
        200: {
            "description": "Reset MSISDN successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 90424242}}},
        },
        404: {
            "description": "Default MSISDN not found for this IMSI.",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    response_model=MSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def reset_msisdn_to_default(imsi: int, verified: bool = Depends(verification)):
    """Set the Default MSISDN for a given IMSI"""
    try:
        return reset_msisdn_by_imsi_to_default(imsi)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Default MSISDN not found for this IMSI.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/imsi/{imsi}/get/default_msisdn",
    summary="Get Default MSISDN",
    responses={
        200: {
            "description": "Default MSISDN retrieved successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 9044242}}},
        },
        404: {
            "description": "Default MSISDN not found for this IMSI.",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    response_model=DefaultMSISDNResponse,
    tags=["IMSI Driven Operations"],
)
async def get_default(imsi: int, verified: bool = Depends(verification)):
    """Get the Default MSISDN for a given IMSI"""
    try:
        return {"imsi": imsi, "default_msisdn": get_default_msisdn_by_imsi(imsi)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Default MSISDN not found for this IMSI.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


""" New HLR functions """
@app.get(
    "/hlr/subscriber/imsi/{imsi}",
    summary="Get Subscriber Info by IMSI",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "imsi not found",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_get_imsi_sub(imsi: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given IMSI"""
    try:
        return {"data": hlr_instance.get_subscriber_by_imsi(imsi)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for IMSI.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/hlr/subscriber/id/{id}",
    summary="Get Subscriber Info by ID",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "ID not found",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_get_id_sub(id: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given ID"""
    try:
        return {"data": hlr_instance.get_subscriber_by_id(id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for ID.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/hlr/subscriber/msisdn/{msisdn}",
    summary="Get Subscriber Info by MSISDN",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "ID not found",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_get_msisdn_sub(msisdn: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given MSISDN"""
    try:
        return {"data": hlr_instance.get_subscriber_by_msisdn(msisdn)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for MSISDN.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/hlr/subscriber/imsi/{imsi}/msisdn",
    summary="Get Subscriber MSISDN by IMSI",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "IMSI not found",
            "content": {"application/json": {"example": {"detail": "Default MSISDN not found for this IMSI."}}},
        },
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_get_imsi_msisdn(msisdn: int, verified: bool = Depends(verification)):
    """Get the subscriber MSISDN for a given IMSI"""
    try:
        return {"data": hlr_instance.get_subscriber_param_by_imsi(msisdn, OsmoSubscriberParam.MSISDN)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for MSISDN.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.post(
    "/hlr/subscriber/imsi/{imsi}/update-msisdn/{msisdn}",
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
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_update_msisdn(imsi: int, msisdn: int, verified: bool = Depends(verification)):
    """Set a new MSISDN for a given IMSI"""
    try:
        return hlr_instance.set_msisdn_by_imsi(imsi, msisdn)
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
    "/hlr/subscriber/create",
    summary="Create new subscriber",
    responses={
        200: {
            "description": "...",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "...",
            "content": {"application/json": {"example": {"detail": "Number already in use. Please try a different number."}}},
        },
        500: DEFAULT_500,
    },
    tags=["HLR Control Interface"],
)
async def hlr_create_new_sub(imsi: int, msisdn: int, cs: bool, ps: bool, verified: bool = Depends(verification)):
    """Set a new MSISDN for a given IMSI"""
    try:
        return hlr_instance.easy_create(imsi, msisdn, cs, ps)
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
    "/msc/active",
    summary="Get Active Subscribers",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
        500: DEFAULT_500,
    },
    tags=["MSC Control Interface"],
)
async def msc_get_active_subs(verified: bool = Depends(verification)):
    try:
        return {"data": msc_instance.list_active_subscribers()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/bsc/param/{param}",
    summary="Get Param",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
        500: DEFAULT_500,
    },
    tags=["BSC Control Interface"],
)
async def bsc_get_params(param: str, verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.get_param(param)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@app.get(
    "/bsc",
    summary="Get BSC status",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
        500: DEFAULT_500,
    },
    tags=["BSC Control Interface"],
)
async def bsc_get_params(verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.easy_get_status()}
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
        500: DEFAULT_500,
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
    "/sim/create/{imsi}/{ki}/{opc}",
    summary="Create SIM in HLR",
    tags=["SIM Operations"],
    responses={
        200: {
            "description": "SIM created successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        500: DEFAULT_500,
    },
)
async def set_create_sim(imsi: int, ki: str, opc: str, verified: bool = Depends(verification)):
    """Creates a New SIM entry in the HLR"""
    try:
        osmo_hlr_run_multiple_elevated(
            [
                f"subscriber imsi {imsi} create",
                f"subscriber imsi {imsi} update msisdn none",
                f"subscriber imsi {imsi} update network-access-mode cs+ps",
                f"subscriber imsi {imsi} update aud3g milenage k {ki} opc {opc}",
            ]
        )
        return {"imsi": imsi, "msisdn": get_default_msisdn_by_imsi(imsi)}
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
        500: DEFAULT_500,
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
