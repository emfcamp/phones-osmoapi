import logging
from enum import IntEnum
from ipaddress import IPv4Address, IPv6Address
from osmoapi import OsmocomController
from typing import Union


# https://osmocom.org/projects/cellular-infrastructure/wiki/Port_Numbers
class OsmoControlInterface(IntEnum):
    BSC = 4249
    MSC = 4255
    HLR = 4259
    CBC = 4265


OSMO_HOST = "127.0.0.1"


class OsmoHLR:

    def __init__(self, host: Union[IPv4Address, IPv6Address, str] = OSMO_HOST, port: int = OsmoControlInterface.HLR):
        self.addr = f"{host}:{port}"

        self.controller = OsmocomController(self.addr)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("logs/osmohlr.log")
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)


class OsmoMSC:

    def __init__(self, host: Union[IPv4Address, IPv6Address, str] = OSMO_HOST, port: int = OsmoControlInterface.MSC):
        self.addr = f"{host}:{port}"

        self.controller = OsmocomController(self.addr)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("logs/osmomsc.log")
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        return self.controller


def get_subscriber_by_imsi(imsi: int):
    hlr = OsmoHLR()
    print(f"subscriber.by-imsi-{imsi}.*")
    print(hlr.controller.get(f"subscriber.by-imsi-{imsi}.info"))
