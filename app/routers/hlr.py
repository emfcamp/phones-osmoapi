from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..dependencies import hlr_instance, security, verification
from ..models import Hex128
from ..osmoctrl import OsmoSubscriberParam

router = APIRouter(
    dependencies=[Depends(security)],
    prefix="/hlr",
    tags=["HLR Control Interface"],
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


class Aud2gUpdate(BaseModel):
    aud2g: Hex128


class HlrSubscriberCreate(BaseModel):
    imsi: int
    msisdn: int
    aud2g: Hex128
    cs: bool
    ps: bool


def _unhandled(e: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An unhandled error occurred: {e}",
    )


@router.get(
    "/subscriber/imsi/{imsi}",
    summary="Get Subscriber Info by IMSI",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "imsi not found",
            "content": {"application/json": {"example": {"detail": "No such subscriber."}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_get_imsi_sub(imsi: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given IMSI"""
    try:
        return {"data": hlr_instance.get_subscriber_by_imsi(imsi)}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for IMSI.",
        )
    except Exception as e:
        raise _unhandled(e)


@router.get(
    "/subscriber/id/{id}",
    summary="Get Subscriber Info by ID",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "ID not found",
            "content": {"application/json": {"example": {"detail": "No such subscriber."}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_get_id_sub(id: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given ID"""
    try:
        return {"data": hlr_instance.get_subscriber_by_id(id)}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for ID.",
        )
    except Exception as e:
        raise _unhandled(e)


@router.get(
    "/subscriber/msisdn/{msisdn}",
    summary="Get Subscriber Info by MSISDN",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "MSISDN not found",
            "content": {"application/json": {"example": {"detail": "No such subscriber."}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_get_msisdn_sub(msisdn: int, verified: bool = Depends(verification)):
    """Get the subscriber info for a given MSISDN"""
    try:
        return {"data": hlr_instance.get_subscriber_by_msisdn(msisdn)}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for MSISDN.",
        )
    except Exception as e:
        raise _unhandled(e)


@router.get(
    "/subscriber/imsi/{imsi}/msisdn",
    summary="Get Subscriber MSISDN by IMSI",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "IMSI not found",
            "content": {"application/json": {"example": {"detail": "No such subscriber."}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_get_imsi_msisdn(imsi: int, verified: bool = Depends(verification)):
    """Get the subscriber MSISDN for a given IMSI"""
    try:
        return {"data": hlr_instance.get_subscriber_param_by_imsi(imsi, OsmoSubscriberParam.MSISDN)}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Info not found for MSISDN.",
        )
    except Exception as e:
        raise _unhandled(e)


@router.post(
    "/subscriber/imsi/{imsi}/update-msisdn/{msisdn}",
    summary="Set New MSISDN for a given IMSI",
    responses={
        200: {
            "description": "Set MSISDN successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "Number already in use. Please try a different number.",
            "content": {"application/json": {"example": {"detail": "Update MSISDN failed"}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_update_msisdn(imsi: int, msisdn: int, verified: bool = Depends(verification)):
    """Set a new MSISDN for a given IMSI"""
    try:
        return hlr_instance.set_msisdn_by_imsi(imsi, msisdn)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Number already in use. Please try a different number.",
        )
    except Exception as e:
        raise _unhandled(e)


@router.post(
    "/subscriber/imsi/{imsi}/update-aud2g",
    summary="Set New aud2g information for a given IMSI",
    responses={
        200: {
            "description": "Set aud2g successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        404: {"description": "No subscriber with that IMSI."},
    },
    tags=["HLR Control Interface"],
)
def hlr_update_aud2g(imsi: int, body: Aud2gUpdate, verified: bool = Depends(verification)):
    """Set a new aud2g (comp128 Ki) for a given IMSI"""
    try:
        aud2g_param = f"{settings.aud2g_algo},{body.aud2g}"
        return hlr_instance.set_aud2g_by_imsi(imsi, aud2g_param)
    except Exception as e:
        raise _unhandled(e)


@router.post(
    "/subscriber/create",
    summary="Create new subscriber in the HLR",
    responses={
        200: {
            "description": "The created subscriber's info.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "IMSI or MSISDN already in use.",
            "content": {"application/json": {"example": {"detail": "Subscriber already exists."}}},
        },
    },
    tags=["HLR Control Interface"],
)
def hlr_create_new_sub(body: HlrSubscriberCreate, verified: bool = Depends(verification)):
    try:
        aud2g_param = f"{settings.aud2g_algo},{body.aud2g}"
        return hlr_instance.easy_create(body.imsi, body.msisdn, body.cs, body.ps, aud2g_param=aud2g_param)
    except Exception as e:
        raise _unhandled(e)
