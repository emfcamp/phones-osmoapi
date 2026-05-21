from pydantic import BaseModel


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


class GetLocationResponse(BaseModel):
    imsi: int = 999430000001234
    lac: int = 12345
    cell_id: int = 1800
    dk: str = "C4"
