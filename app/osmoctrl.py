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


class OsmoComponent:
    """Base class handling shared Osmocom controller initialization and logging."""
    
    def __init__(self, host: Union[IPv4Address, IPv6Address, str], port: int, log_filename: str):
        self.addr = f"{host}:{port}"
        self.controller = OsmocomController(self.addr)
        self.logger = None
        self._setup_logging(log_filename)
    
    def _setup_logging(self, log_filename: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)#

        handler = logging.FileHandler(f"logs/{log_filename}")
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)


class OsmoHLR(OsmoComponent):

    def __init__(self, host: Union[IPv4Address, IPv6Address, str] = OSMO_HOST, port: int = OsmoControlInterface.HLR):
        super().__init__(host, port, "osmohlr.log")
    
    def get_subscriber_by_imsi(self, imsi: int):
        self.logger.info(f"OsmoHLR> subscriber.by-imsi-{imsi}.info")
        resp = self.controller.get(f"subscriber.by-imsi-{imsi}.info")
        self.logger.debug(resp)
        
        lines = resp.splitlines()
        info = {}
        for line in lines:
            if not line.strip(): 
                continue
            ld = line.split("\t")
            if len(ld) >= 2:
                info[ld[0]] = ld[1]
        return info


class OsmoMSC(OsmoComponent):

    def __init__(self, host: Union[IPv4Address, IPv6Address, str] = OSMO_HOST, port: int = OsmoControlInterface.MSC):
        super().__init__(host, port, "osmomsc.log")

    def list_active_subscribers(self):
        self.logger.info("OsmoMSC> subscriber-list-active-v1")
        resp = self.controller.get("subscriber-list-active-v1")
        print(resp)
        return resp
