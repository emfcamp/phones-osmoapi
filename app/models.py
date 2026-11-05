import unicodedata
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


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
    dk: str | None = "C4"


IdentifierKind = Literal["msisdn", "extension", "imsi", "tmsi", "id"]


def no_control_chars(value: str) -> str:
    """Reject control characters (CR, LF, TAB, ESC, ^C, ^Z, ...)."""
    if any(unicodedata.category(c) == "Cc" for c in value):
        raise ValueError("must not contain control characters (including newlines)")
    return value


SubscriberIdValue = Annotated[str, Field(pattern=r"^(?:\d{1,15}|0x[0-9a-fA-F]{1,8})$")]
VtyLine = Annotated[str, Field(min_length=1), AfterValidator(no_control_chars)]


class SubscriberId(BaseModel):
    kind: IdentifierKind
    value: SubscriberIdValue

    def __str__(self):
        return f"{self.kind} {self.value}"


class SendSmsRequest(BaseModel):
    recipient: SubscriberId
    sender: SubscriberId
    message: VtyLine
