from typing import Annotated, Literal, Optional
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel, Field
from ..config import settings
from ..dependencies import bearer_scheme, hlr_instance, verify_core_token
from ..osmoctrl import OsmoSubscriberParam


router = APIRouter(
    dependencies=[Depends(bearer_scheme)],
    prefix="/emf",
    tags=["EMF Core"],
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


class CoreWebhookBody(BaseModel):
    event: Literal["bind", "unbind", "properties"]
    service: str
    vanityNumber: int
    tempNumber: int
    properties: dict


def hlr_bind(body: CoreWebhookBody):
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

    return Response(status_code=status.HTTP_502_BAD_GATEWAY)


def hlr_unbind(body: CoreWebhookBody):
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

    return Response(status_code=status.HTTP_502_BAD_GATEWAY)


def hlr_props(body: CoreWebhookBody):
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

    return Response(status_code=status.HTTP_502_BAD_GATEWAY)


@router.post(
    "/core-webhook",
    summary="Webhook for binding/unbinding/properties",
)
async def core_webhook(body: CoreWebhookBody, verified: bool = Depends(verify_core_token)):
    if body.service.lower() != "gsm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported service type",
        )

    handlers = {
        "bind": hlr_bind,
        "unbind": hlr_unbind,
        "properties": hlr_props,
    }
    handler = handlers[body.event]

    try:
        return handler(body)
    except HTTPException:
        # Already a well-formed client/upstream error — re-raise as-is.
        raise
    except Exception:
        # Log full detail server-side, but never leak internals to the caller.
        logger.exception("Unhandled error processing %s event", body.event)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the webhook",
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
    ki: str = Field(min_length=32, max_length=32)
    opc: str = Field(min_length=32, max_length=32)
    gprsEnabled: bool
    lteEnabled: bool


class SimUpdate(BaseModel):
    msisdn: int
    ki: str = Field(min_length=32, max_length=32)
    opc: str = Field(min_length=32, max_length=32)
    gprsEnabled: bool
    lteEnabled: bool


@router.post("/sim", summary="Create Subscriber")
@handle_hlr_errors
async def create_sim(body: SimCreate):
    aud2g_param = build_aud2g_param(body.ki)
    subscriber = hlr_instance.easy_create(body.imsi, body.msisdn, True, body.gprsEnabled)
    hlr_instance.set_aud2g_by_imsi(body.imsi, aud2g_param)

    # TODO: If lteEnabled create SIM in open5gs database

    return subscriber


@router.get("/sim/{imsi}", summary="")
@handle_hlr_errors
async def fetch_sim(imsi: int):
    ## TODO: Check if SIM is in open5gs database

    return hlr_instance.get_subscriber_by_imsi(imsi)


@router.patch("/sim/{imsi}", summary="")
@handle_hlr_errors
async def update_sim(imsi: int, body: SimUpdate):
    aud2g_param = build_aud2g_param(body.ki)
    hlr_instance.set_aud2g_by_imsi(imsi, aud2g_param)
    hlr_instance.set_msisdn_by_imsi(imsi, body.msisdn)
    hlr_instance.set_ps_by_imsi(imsi, body.gprsEnabled)

    ## TODO: Check lteEnabled state against open5gs database

    return hlr_instance.get_subscriber_by_imsi(imsi)


@router.delete("/sim/{imsi}", summary="")
@handle_hlr_errors
async def delete_sim(imsi: int):
    ## TODO: Delete from open5gs database

    return hlr_instance.delete_subscriber(imsi)
