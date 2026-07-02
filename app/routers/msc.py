from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import msc_instance, security, verification


router = APIRouter(
    dependencies=[Depends(security)],
    prefix="/msc",
    tags=["MSC Control Interface"],
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
    "/active",
    summary="Get Active Subscribers",
    responses={
        200: {
            "description": "success",
            "content": {"application/json": {}},
        },
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
