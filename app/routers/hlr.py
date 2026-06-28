from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..config import settings
from ..dependencies import hlr_instance, security, verification
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
            "content": {"application/json": {"example": {"detail": "Subscriber information not found for imsi."}}},
        },
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
            "content": {"application/json": {"example": {"detail": "Subscriber info not found for ID"}}},
        },
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


@router.get(
    "/subscriber/msisdn/{msisdn}",
    summary="Get Subscriber Info by MSISDN",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "default_msisdn": 9044242}}},
        },
        404: {
            "description": "ID not found",
            "content": {"application/json": {"example": {"detail": "Subscriber information not found for MSISDN"}}},
        },
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
            "content": {"application/json": {"example": {"detail": "MSISDN not found for imsi"}}},
        },
    },
    tags=["HLR Control Interface"],
)
async def hlr_get_imsi_msisdn(imsi: int, verified: bool = Depends(verification)):
    """Get the subscriber MSISDN for a given IMSI"""
    try:
        return {"data": hlr_instance.get_subscriber_param_by_imsi(imsi, OsmoSubscriberParam.MSISDN)}
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
            "content": {"application/json": {"example": {"detail": "Number already in use. Please try a different number."}}},
        },
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


@router.post(
    "/subscriber/imsi/{imsi}/update-aud2g/{msisdn}",
    summary="Set New aud2g information for a given IMSI",
    responses={
        200: {
            "description": "Set aud2g successfully.",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
    },
    tags=["HLR Control Interface"],
)
async def hlr_update_aud2g(imsi: int, aud2g: Annotated[str | None, Query(min_length=32, max_length=32)], verified: bool = Depends(verification)):
    """Set a new aud2g for a given IMSI"""
    try:
        aud2g_param = f"{settings.aud2g_algo},{aud2g}"
        return hlr_instance.set_aud2g_by_imsi(imsi, aud2g_param)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@router.post(
    "/subscriber/create",
    summary="Create new subscriber in the HLR",
    responses={
        200: {
            "description": "...",
            "content": {"application/json": {"example": {"imsi": 999430000001234, "msisdn": 4242}}},
        },
        409: {
            "description": "...",
            "content": {"application/json": {"example": {"detail": "Number already in use. Please try a different number."}}},
        },
    },
    tags=["HLR Control Interface"],
)
async def hlr_create_new_sub(
    imsi: int,
    msisdn: int,
    aud2g: Annotated[str | None, Query(min_length=32, max_length=32)],
    cs: bool,
    ps: bool,
    verified: bool = Depends(verification),
):
    try:
        aud2g_param = f"{settings.aud2g_algo},{aud2g}"
        return hlr_instance.easy_create(imsi, msisdn, aud2g_param, cs, ps)
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
