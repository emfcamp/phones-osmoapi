from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import bsc_instance, security, verification


router = APIRouter(
    dependencies=[Depends(security)],
    prefix="/bsc",
    tags=["BSC Control Interface"],
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
    "/param/{param}",
    summary="Get BSC Parameter",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
    },
)
async def bsc_get_params(param: str, verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.get_param(param)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@router.get(
    "/",
    summary="Get BSC status information",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
    },
)
async def bsc_get_status(verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.easy_get_status()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@router.get(
    "/bts/{bts_n}",
    summary="Get BTS information",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
    },
)
async def bts_get_info(bts_n: int, verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.easy_get_bts_info(bts_n)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )


@router.post(
    "/restart-all",
    summary="Restart all BTSes",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
    },
)
async def bsc_restart_bts(verified: bool = Depends(verification)):
    try:
        return {"data": bsc_instance.restart_bts()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unhandled error occurred: {e}",
        )
