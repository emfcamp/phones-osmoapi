import re

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Literal, Union
from pydantic import BaseModel

from ..dependencies import dks, security, verification
from ..msisdn import (
    get_all_default_msisdn,
    get_all_subscribers_from_hlr,
    get_default_msisdn_by_imsi,
)
from ..models import *
from ..osmo import (
    osmo_hlr_run_multiple_elevated,
    osmo_hlr_run_single,
    osmo_msc_run_single,
    osmo_msc_run_single_elevated,
)


router = APIRouter(
    dependencies=[Depends(security)],
    prefix="/telnet",
    tags=["Telnet Interface"],
    responses={
        500: {
            "description": "An unhandled error occurred.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An unhandled error occurred. Error: Something went wrong.",
                    }
                }
            },
        },
    },
)


@router.get(
    "/get_all_default_msisdns",
    summary="Get All Default MSISDNs for Known IMSIs",
    responses={
        200: {
            "description": "Default MSISDNs retrieved successfully.",
            "content": {"application/json": {"example": {"default_msisdns": [4242, 4243, 4244]}}},
        },
    },
    response_model=AllDefaultMSISDNResponse,
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


@router.get(
    "/get_all_hlr_msisdns",
    summary="Get All MSISDNs known to the HLR",
    responses={
        200: {
            "description": "HLR MSISDNs retrieved successfully.",
            "content": {"application/json": {"example": {"msisdns": [4242, 4243, 4244]}}},
        },
    },
    response_model=AllMSISDNResponse,
)
async def get_all_hlr_msisdns(verified: bool = Depends(verification)):
    """Get all MSISDNs known to HLR"""
    try:
        subsribers = get_all_subscribers_from_hlr()
        return {"msisdns": [row["msisdn"] for row in subscribers]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@router.get(
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
    },
    response_model=DefaultMSISDNResponse,
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


@router.get(
    "/imsi/{imsi}/get/location",
    summary="Get Location Information",
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
    },
    response_model=GetLocationResponse,
)
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


@router.get(
    "/get-hlr-subscribers",
    summary="Get all HLR subscriber information",
)
async def get_all_hlr_subscribers():
    try:
        return get_all_subscribers_from_hlr()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


IdentifierKind = Literal["msisdn", "extension", "imsi", "tmsi", "id"]


class SubscriberId(BaseModel):
    kind: IdentifierKind
    value: str

    def __str__(self):
        return f"{self.kind} {self.value}"


def send_sms(recipient: SubscriberId, sender: SubscriberId, message: str):
    """
    ### subscriber(msisdn|extension|imsi|tmsi|id) ID sms sender(msisdn|extension|imsi|tmsi|id) SENDER_ID send LINE
    # % No subscriber found for msisdn 9990000
    """
    cmd = f"subscriber {recipient} sms sender {sender} send {message}"
    return osmo_msc_run_single_elevated(cmd)


class SendSmsRequest(BaseModel):
    recipient: SubscriberId
    sender: SubscriberId
    message: str


@router.post(
    "/sms/send",
    summary="Send SMS to subscriber, both sender and recipient must be connected to MSC.",
)
def api_send_sms(payload: SendSmsRequest):
    raw = osmo_msc_run_single_elevated(f"show sms-queue")
    try:
        return {"result": send_sms(payload.recipient, payload.sender, payload.message)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
