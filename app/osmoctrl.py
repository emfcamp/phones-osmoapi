import logging
import socket
from enum import IntEnum, StrEnum
from ipaddress import IPv4Address, IPv6Address
from os import environ, makedirs

from osmoapi import OsmocomController

from .config import settings


# https://osmocom.org/projects/cellular-infrastructure/wiki/Port_Numbers
class OsmoControlInterface(IntEnum):
    BSC = 4249
    MSC = 4255
    HLR = 4259
    CBC = 4265
    MGW = 4267


OSMO_HOST = environ.get("OSMOCOM_HOST", "127.0.0.1")


def jsonify_response(resp: str):
    lines = resp.splitlines()
    data = {}
    for line in lines:
        if not line.strip():
            continue
        ld = line.split("\t")
        if len(ld) >= 2:
            data[ld[0]] = ld[1]
    return data


class OsmoComponent:
    """Base class handling shared Osmocom controller initialization and logging."""

    def __init__(self, host: IPv4Address | IPv6Address | str, port: int, log_filename: str):
        self.addr = f"{host}:{port}"
        self.controller = OsmocomController(self.addr)
        self.logger = None
        self._setup_logging(log_filename)

    def _setup_logging(self, log_filename: str):
        makedirs(f"{settings.logs_dir}/", exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt="%(asctime)s [%(classname)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler = logging.FileHandler(f"{settings.logs_dir}/{log_filename}")
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        self.logger.addHandler(handler)
        self.logger = logging.LoggerAdapter(self.logger, {"classname": self.__class__.__name__})

    def _get(self, cmd: str):
        self.logger.info(cmd)

        try:
            resp = self.controller.get(cmd)
            self.logger.debug(resp)
            return resp
        except Exception as e:
            self.logger.error(f"[Exception]-> {e}")

        return {}

    def _get_kv(self, cmd: str):
        self.logger.info(cmd)

        try:
            resp = self.controller.get(cmd)
            self.logger.debug(resp)
            return jsonify_response(resp)
        except Exception as e:
            self.logger.error(f"[Exception]-> {e}")

        return {}

    def _set(self, cmd: str, val: int):
        self.logger.info(cmd)

        try:
            resp = self.controller.set(cmd, str(val))
            self.logger.info(resp)
            return resp
        except Exception as e:
            self.logger.error(f"[Exception]-> {e}")

        return ""

    def _alive(self) -> bool:
        host, port = self.addr.split(":")
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            return False


# https://downloads.osmocom.org/docs/osmo-bsc/master/osmobsc-usermanual.pdf
class OsmoBSC(OsmoComponent):
    def __init__(self, host: IPv4Address | IPv6Address | str = OSMO_HOST, port: int = OsmoControlInterface.BSC):
        super().__init__(host, port, "osmobsc.log")

    def get_param(self, param):
        return self._get(param)

    def set_param(self, param, val):
        return self._set(param, val)

    def easy_get_status(self):
        status_keys = ["msc_connection_status", "bts_connection_status", "timezone", "location", "rf_locked", "mcc", "mnc", "number-of-bts"]
        return {key: self.get_param(key) for key in status_keys}

    def easy_get_bts_info(self, bts_n: int):
        status_keys = [
            "channel-load",
            "oml-uptime",
            "rf_state",
            "location-area-code",
            "cell-identity",
            "bsic",
        ]
        data = {key: self.get_param(f"bts.{bts_n}.{key}") for key in status_keys}

        channel_loads = data["channel-load"].split()
        data["channel-load"] = {}
        for channel_load in channel_loads:
            key, used, total = channel_load.split(",")
            data["channel-load"][key] = f"{used}/{total}"

        return data

    def restart_bts(self):
        """Restart all BTSes"""
        return self.set_param("apply-configuration", "restart")


class OsmoSubscriberParam(StrEnum):
    AUD2G = "aud2g"
    AUD3G = "aud3g"
    MSISDN = "msisdn"
    CS = "cs-enabled"
    PS = "ps-enabled"


class OsmoHLR(OsmoComponent):
    def __init__(self, host: IPv4Address | IPv6Address | str = OSMO_HOST, port: int = OsmoControlInterface.HLR):
        super().__init__(host, port, "osmohlr.log")

    def get_subscriber_by_id(self, sub_id: int):
        return self._get_kv(f"subscriber.by-id-{sub_id}.info")

    def get_subscriber_by_imsi(self, imsi: int):
        return self._get_kv(f"subscriber.by-imsi-{imsi}.info")

    def get_subscriber_by_msisdn(self, msisdn: int):
        return self._get_kv(f"subscriber.by-msisdn-{msisdn}.info")

    ## Get parameter value
    def get_subscriber_param_by_id(self, sub_id: int, param: OsmoSubscriberParam):
        return self._get(f"subscriber.by-id-{sub_id}.{param.value}")

    def get_subscriber_param_by_imsi(self, imsi: int, param: OsmoSubscriberParam):
        return self._get(f"subscriber.by-imsi-{imsi}.{param.value}")

    ## IMSI operations
    def create_subscriber(self, imsi: int) -> int:
        """Create a subscriber in the HLR with the IMSI specified, returns the ID of the created subscriber"""
        return self._set("subscriber.create", imsi)

    def delete_subscriber(self, imsi: int) -> int:
        """Deletes a subscriber with the imsi specified from the HLR, returns the ID of the deleted subscriber"""
        return self._set("subscriber.delete", imsi)

    ## MSISDN
    def set_msisdn_by_id(self, sub_id: int, msisdn: int):
        return self._set(f"subscriber.by-id-{sub_id}.msisdn", msisdn)

    def set_msisdn_by_imsi(self, imsi: int, msisdn: int):
        return self._set(f"subscriber.by-imsi-{imsi}.msisdn", msisdn)

    ## aud2g: algo[,KI]
    def set_aud2g_by_id(self, sub_id: int, aud2g: str):
        return self._set(f"subscriber.by-id-{sub_id}.aud2g", aud2g)

    def set_aud2g_by_imsi(self, imsi: int, aud2g: str):
        return self._set(f"subscriber.by-imsi-{imsi}.aud2g", aud2g)

    ## aud3g: algo[,KI,("op"|"opc"),OP_C[,ind_bitlen]]
    def set_aud3g_by_id(self, sub_id: int, aud3g: str):
        return self._set(f"subscriber.by-id-{sub_id}.aud3g", aud3g)

    def set_aud3g_by_imsi(self, imsi: int, aud3g: str):
        return self._set(f"subscriber.by-imsi-{imsi}.aud3g", aud3g)

    ## CS
    def set_cs_by_id(self, sub_id: int, enabled: bool = True):
        value = 1 if enabled else 0
        return self._set(f"subscriber.by-id-{sub_id}.cs-enabled", value)

    def set_cs_by_imsi(self, imsi: int, enabled: bool = True):
        value = 1 if enabled else 0
        return self._set(f"subscriber.by-imsi-{imsi}.cs-enabled", value)

    ## PS
    def set_ps_by_id(self, sub_id: int, enabled: bool = True):
        value = 1 if enabled else 0
        return self._set(f"subscriber.by-id-{sub_id}.ps-enabled", value)

    def set_ps_by_imsi(self, imsi: int, enabled: bool = True):
        value = 1 if enabled else 0
        return self._set(f"subscriber.by-imsi-{imsi}.ps-enabled", value)

    ## Easy operations
    def easy_create(self, imsi: int, msisdn: int, aud2g_param: str, cs: bool, ps: bool) -> dict:
        """Single function to create subscriber with all params"""
        ## TODO: Check if msisdn already exists and throw a different error

        _id = self.create_subscriber(imsi)
        if self.set_msisdn_by_id(_id, msisdn) != "OK":
            logging.error(f"Failed to set msisdn for newly created subscriber ID {_id}")
            return f"Failed to set msisdn for newly created subscriber ID {_id}"

        self.set_aud2g_by_id(_id, aud2g_param)
        
        self.set_cs_by_id(_id, cs)
        self.set_ps_by_id(_id, ps)

        return self.get_subscriber_by_id(_id)


class OsmoMSC(OsmoComponent):
    def __init__(self, host: IPv4Address | IPv6Address | str = OSMO_HOST, port: int = OsmoControlInterface.MSC):
        super().__init__(host, port, "osmomsc.log")

    def list_active_subscribers(self):
        return self._get_kv("subscriber-list-active-v1")


## TODO: use to get rate-counters
class OsmoMGW(OsmoComponent):
    def __init__(self, host: IPv4Address | IPv6Address | str = OSMO_HOST, port: int = OsmoControlInterface.MGW):
        super().__init__(host, port, "osmomgw.log")
