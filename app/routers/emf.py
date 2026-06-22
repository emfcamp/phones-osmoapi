from typing import Annotated
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel, Field
from ..config import settings
from ..dependencies import bearer_scheme, verify_bearer_token
from ..osmoctrl import OsmoHLR, OsmoSubscriberParam


hlr_instance = OsmoHLR()

router = APIRouter(
    dependencies=[Depends(bearer_scheme)],
    prefix="/emf",
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

"""
{
  "event": "bind",
  "service": "GSM",
  "vanityNumber": 2002,
  "tempNumber": 19050000,
  "properties": {
    "ps": true
  }
}
"""


def hlr_bind(body: dict):
    ## find tempNumber in db and replace with vanityNumber
    old_number = body.get("tempNumber")
    new_number = body.get("vanityNumber")

    subscriber_info = hlr_instance.get_subscriber_by_msisdn(old_number)
    imsi = subscriber_info.get("imsi")
    print(f"Updating subscriber with {imsi=} MSISDN from {old_number} to {new_number}")

    result = hlr_instance.set_msisdn_by_imsi(imsi, new_number)
    print(result)
    if result == "OK":
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def hlr_unbind(body: dict):
    ## find vanityNumber in db and replace with tempNumber
    old_number = body.get("vanityNumber")
    new_number = body.get("tempNumber")

    subscriber_info = hlr_instance.get_subscriber_by_msisdn(old_number)
    imsi = subscriber_info.get("imsi")
    print(f"Updating subscriber with {imsi=} MSISDN from {old_number} to {new_number}")

    result = hlr_instance.set_msisdn_by_imsi(imsi, new_number)
    print(result)
    if result == "OK":
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def hlr_props(body: dict):
    DEFAULT_PROPS = {"ps": True}

    vanity_number = body.get("vanityNumber")
    temp_number = body.get("tempNumber")
    properties = body.get("properties", DEFAULT_PROPS)

    subscriber_info = hlr_instance.get_subscriber_by_msisdn(vanity_number)
    if not subscriber_info:
        subscriber_info = hlr_instance.get_subscriber_by_msisdn(temp_number)
        if not subscriber_info:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    imsi = subscriber_info.get("imsi")
    result = hlr_instance.set_ps_by_imsi(imsi, properties.get("ps", True))
    if result == "OK":
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/core-webhook",
    summary="",
    tags=["Core"],
)
async def core_webhook(body: dict, verified: bool = Depends(verify_bearer_token)):
    try:
        if body.get("service", "").lower() != "gsm":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"wrong service type",
            )

        if body.get("event") == "bind":
            return hlr_bind(body)
        elif body.get("event") == "unbind":
            return hlr_unbind(body)
        elif body.get("event") == "properties":
            return hlr_props(body)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"wrong event type",
            )

        return "OK"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


def build_aud2g_param(aud2g: str) -> str:
    return f"{settings.aud2g_algo},{aud2g}"


def handle_hlr_errors(fn):
    """Wraps HLR calls so all endpoints get consistent error handling."""

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Number already in use. Please try a different number.",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unhandled error occurred: {e}",
            )

    return wrapper


class SimCreate(BaseModel):
    imsi: int
    msisdn: int
    aud2g: str = Field(min_length=32, max_length=32)


class SimUpdate(BaseModel):
    msisdn: int
    aud2g: str = Field(min_length=32, max_length=32)


@router.post("/sim", summary="Create Subscriber")
@handle_hlr_errors
async def create_sim(body: SimCreate):
    aud2g_param = build_aud2g_param(body.aud2g)
    subscriber = hlr_instance.easy_create(body.imsi, body.msisdn, True, False)
    hlr_instance.set_aud2g_by_imsi(body.imsi, aud2g_param)
    return subscriber


@router.get("/sim/{imsi}", summary="")
@handle_hlr_errors
async def fetch_sim(imsi: int):
    return hlr_instance.get_subscriber_by_imsi(imsi)


@router.patch("/sim/{imsi}", summary="")
@handle_hlr_errors
async def update_sim(imsi: int, body: SimUpdate):
    aud2g_param = build_aud2g_param(body.aud2g)
    hlr_instance.set_aud2g_by_imsi(imsi, aud2g_param)
    hlr_instance.set_msisdn_by_imsi(imsi, body.msisdn)
    return hlr_instance.get_subscriber_by_imsi(imsi)  # fixed: was self.get_subscriber_by_id(id)


@router.delete("/sim/{imsi}", summary="")
@handle_hlr_errors
async def delete_sim(imsi: int):
    return hlr_instance.delete_subscriber(imsi)
