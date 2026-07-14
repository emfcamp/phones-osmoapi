from datetime import datetime
from typing import Annotated, Literal, Optional
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel, Field
from ..config import settings
from ..dependencies import bearer_scheme, verify_core_token
from ..models import SubscriberId
from ..osmo import send_sms
from ..pyhss_client import pyhss_client, PyHSSError


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


async def hlr_bind(body: CoreWebhookBody):
    ## find tempNumber in db and replace with vanityNumber
    old_number = body.tempNumber
    new_number = body.vanityNumber
    print(f"Updating number from {old_number} to {new_number}")

    subscriber_info = await pyhss_client.get_subscriber_by_msisdn(old_number)
    print(subscriber_info)
    if not subscriber_info:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    imsi = subscriber_info.get("imsi")
    subscriber_id = subscriber_info.get("subscriber_id")
    if not imsi or subscriber_id is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    print(f"Updating subscriber with {imsi=} MSISDN from {old_number} to {new_number}")

    try:
        await pyhss_client.update_subscriber(subscriber_id, msisdn=str(new_number))
        success = True
    except PyHSSError as e:
        print(e)
        success = False

    if success:
        try:
            send_sms(
                SubscriberId(kind="imsi", value=imsi),
                SubscriberId(kind="imsi", value=imsi),
                message=f"Your number will now change from {old_number} to {new_number} when you turn your phone off and on again, or turn airplane mode on for at least 10s.",
            )
        except Exception as e:
            print(e)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    now = datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        send_sms(
            SubscriberId(kind="imsi", value=imsi),
            SubscriberId(kind="imsi", value=imsi),
            message=f"There was an error with your request to 191 at {datetime_str} - EMF",
        )
    except Exception as e:
        print(e)

    return Response(status_code=status.HTTP_502_BAD_GATEWAY)


async def hlr_unbind(body: CoreWebhookBody):
    ## find vanityNumber in db and replace with tempNumber
    old_number = body.vanityNumber
    new_number = body.tempNumber
    print(f"Updating number from {old_number} to {new_number}")

    subscriber_info = await pyhss_client.get_subscriber_by_msisdn(old_number)
    if not subscriber_info:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    imsi = subscriber_info.get("imsi")
    subscriber_id = subscriber_info.get("subscriber_id")
    if not imsi or subscriber_id is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    print(f"Updating subscriber with {imsi=} MSISDN from {old_number} to {new_number}")

    try:
        await pyhss_client.update_subscriber(subscriber_id, msisdn=str(new_number))
        success = True
    except PyHSSError as e:
        print(e)
        success = False

    if success:
        try:
            send_sms(
                SubscriberId(kind="imsi", value=imsi),
                SubscriberId(kind="imsi", value=imsi),
                message=f"Your number will now change from {old_number} to {new_number} when you turn your phone off and on again, or turn airplane mode on for at least 10s.",
            )
        except Exception as e:
            print(e)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    now = datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        send_sms(
            SubscriberId(kind="imsi", value=imsi),
            SubscriberId(kind="imsi", value=imsi),
            message=f"There was an error with your request to 191 at {datetime_str} - EMF",
        )
    except Exception as e:
        print(e)

    return Response(status_code=status.HTTP_502_BAD_GATEWAY)


async def hlr_props(body: CoreWebhookBody):
    vanity_number = body.vanityNumber
    temp_number = body.tempNumber
    properties = body.properties

    subscriber_info = await pyhss_client.get_subscriber_by_msisdn(vanity_number)
    if not subscriber_info:
        subscriber_info = await pyhss_client.get_subscriber_by_msisdn(temp_number)
        if not subscriber_info:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    subscriber_id = subscriber_info.get("subscriber_id")
    if subscriber_id is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    try:
        await pyhss_client.update_subscriber(subscriber_id)
    except PyHSSError as e:
        print(e)
        return Response(status_code=status.HTTP_502_BAD_GATEWAY)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/core-webhook",
    summary="Webhook for binding/unbinding/properties",
    responses={
        204: {"description": "Success (probably)"},
        401: {"description": "Authentication token was not set"},
        404: {"description": "Subscriber not found"},
        502: {"description": "Request failed."},
    },
)
async def core_webhook(body: CoreWebhookBody, verified: bool = Depends(verify_core_token)):
    if body.service.lower() != "gsm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported service type",
        )
    print(body)

    handlers = {
        "bind": hlr_bind,
        "unbind": hlr_unbind,
        "properties": hlr_props,
    }
    handler = handlers[body.event]

    try:
        return await handler(body)
    except HTTPException:
        # Already a well-formed client/upstream error - re-raise as-is.
        raise
    except Exception as e:
        print(e)
        print(f"Unhandled error processing {body.event} event")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the webhook",
        )


def handle_hlr_errors(fn):
    """Wraps pyHSS calls so all endpoints get consistent error handling."""

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except PyHSSError as e:
            if e.status_code in (400, 409):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Number already in use, or the request was rejected by pyHSS. Please try different values.",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"pyHSS request failed: {e}",
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
    imsi: str
    iccid: str
    msisdn: int
    ki: str = Field(min_length=32, max_length=32)
    opc: str = Field(min_length=32, max_length=32)
    gprsEnabled: bool
    name: Optional[str]


class SimUpdate(BaseModel):
    imsi: str
    iccid: str
    msisdn: int
    ki: str = Field(min_length=32, max_length=32)
    opc: str = Field(min_length=32, max_length=32)
    gprsEnabled: bool
    name: Optional[str]


@router.post("/sim", summary="Create Subscriber")
async def create_sim(body: SimCreate):
    print(body)
    print(f"Creating SIM {body.iccid=} {body.name=}")
    auc_imsi_lookup = await pyhss_client.get_auc_by_imsi(body.imsi)
    auc_iccid_lookup = await pyhss_client.get_auc_by_iccid(body.iccid)
    sub_imsi_lookup = await pyhss_client.get_subscriber_by_imsi(body.imsi)

    if sub_imsi_lookup or auc_imsi_lookup:
        print(f"Tried to create subscriber with IMSI {body.imsi} but they're already in the database")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IMSI already exists in subscriber database!")

    if auc_iccid_lookup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IMSI or ICCID already exist in database.")

    print(f"Creating AuC for subscriber...")
    auc = await pyhss_client.create_auc(
        {
            "imsi": body.imsi,
            "iccid": body.iccid,
            "sqn": 0,
            "ki": body.ki,
            "opc": body.opc,
            "amf": settings.pyhss_default_amf,
            "algo": settings.pyhss_2g_algo,
        }
    )

    subscriber_payload = {
        "imsi": str(body.imsi),
        "enabled": True,
        "auc_id": auc["auc_id"],
        "msisdn": str(body.msisdn),
        "default_apn": settings.pyhss_default_apn_id,
        "apn_list": str(settings.pyhss_default_apn_id),
    }
    try:
        print(f"Creating subscriber...")
        subscriber = await pyhss_client.create_subscriber(subscriber_payload)
    except:
        ## Failed to create subscriber so delete auc so we are not left with un-associated key information
        pyhss_client.delete_auc(auc["auc_id"])

    # Set name attribute
    if body.name:
        try:
            print(f"Assigning subscriber name...")
            subscriber_name = await pyhss_client.create_subscriber_attribute(
                {
                    "subscriber_id": subscriber["subscriber_id"],
                    "key": "subscriberName",
                    "value": str(body.name),
                }
            )
        except Exception as e:
            print("Failed to assign subscriber name, ignoring...")

    print(subscriber)

    return {
        "auc_id": subscriber["auc_id"],
        "subscriber_id": subscriber["subscriber_id"],
    }


@router.get("/sim/{subscriber_id}", summary="Fetch SIM information from pyHSS by subscriber_id")
@handle_hlr_errors
async def fetch_sim_by_subscriberid(subscriber_id: int):
    subscriber = await pyhss_client.get_subscriber(subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriber not found")

    return subscriber


@router.get("/sim/imsi/{imsi}", summary="Fetch SIM information from pyHSS by imsi")
@handle_hlr_errors
async def fetch_sim_by_imsi(imsi: int):
    subscriber = await pyhss_client.get_subscriber_by_imsi(imsi)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriber not found")

    return subscriber


@router.patch("/sim/{subscriber_id}", summary="Update SIM information from pyHSS by subscriber_id")
@handle_hlr_errors
async def update_sim_by_subscriberid(subscriber_id: int, body: SimUpdate):
    print(body)
    subscriber = await pyhss_client.get_subscriber(subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriber not found")

    await pyhss_client.update_auc(subscriber["auc_id"], ki=body.ki, opc=body.opc, imsi=body.imsi, iccid=body.iccid)

    updated = await pyhss_client.update_subscriber(
        subscriber["subscriber_id"],
        msisdn=str(body.msisdn),
        default_apn=settings.pyhss_default_apn_id,
        apn_list=str(settings.pyhss_default_apn_id),
    )

    ## Subscriber attributes
    attributes = await pyhss_client.get_subscriber_attributes(subscriber["subscriber_id"])
    subscriber_attribute_id = next((item["subscriber_attributes_id"] for item in attributes if item["key"] == "subscriberName"), None)
    if subscriber_attribute_id:
        await pyhss_client.update_subscriber_attribute(subscriber_attribute_id, key="subscriberName", value=str(body.name))
    else:
        await pyhss_client.create_subscriber_attribute(
            {
                "subscriber_id": subscriber["subscriber_id"],
                "key": "subscriberName",
                "value": str(body.name),
            }
        )

    print(updated)
    return {
        "auc_id": subscriber["auc_id"],
        "subscriber_id": subscriber["subscriber_id"],
    }


@router.delete("/sim/{subscriber_id}", summary="Delete subscriber_id and AuC from pyHSS")
@handle_hlr_errors
async def delete_sim(subscriber_id: int):
    subscriber = await pyhss_client.get_subscriber(subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriber not found")

    attributes = await pyhss_client.get_subscriber_attributes(subscriber["subscriber_id"])
    for attribute in attributes:
        await pyhss_client.delete_subscriber_attribute(attribute["subscriber_attributes_id"])

    result = await pyhss_client.delete_subscriber(subscriber["subscriber_id"])
    auc_id = subscriber.get("auc_id")
    if auc_id is not None:
        await pyhss_client.delete_auc(auc_id)

    if result["Result"] == "OK":
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    print(result)
    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/list-subscribers", summary="Fetch subscribers")
@handle_hlr_errors
async def fetch_subscriber_list():
    subscribers = await pyhss_client.get_subscribers()

    output = []
    for subscriber in subscribers:
        output.append(
            {
                "auc_id": subscriber["auc_id"],
                "subscriber_id": subscriber["subscriber_id"],
                "imsi": subscriber["imsi"],
                "msisdn": subscriber["msisdn"],
            }
        )

    return output
