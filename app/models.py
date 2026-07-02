from pydantic import BaseModel
from typing import Literal, Union


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


IdentifierKind = Literal["msisdn", "extension", "imsi", "tmsi", "id"]


class SubscriberId(BaseModel):
    kind: IdentifierKind
    value: str

    def __str__(self):
        return f"{self.kind} {self.value}"


class SendSmsRequest(BaseModel):
    recipient: SubscriberId
    sender: SubscriberId
    message: str
