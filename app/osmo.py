import logging
from ipaddress import IPv4Address, IPv6Address
from telnetlib3 import Telnet
from typing import Union
from .models import SendSmsRequest, SubscriberId


class OsmocomHLR:
    def __init__(self, host: Union[IPv4Address, IPv6Address, str], port: int):
        self.host = host
        self.port = port
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("osmo_hlr.log")
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def connect(self):
        self.session = Telnet(str(self.host), self.port)
        self.session.read_until(b"OsmoHLR> ", timeout=5)
        self.logger.info(f"Connected to {self.host}:{self.port}")

    def disconnect(self):
        if self.session:
            self.session.close()
            self.logger.info(f"Disconnected from {self.host}:{self.port}")

    def enable(self):
        if self.session:
            self.session.write(b"enable\n")
            self.session.read_until(b"OsmoHLR# ", timeout=5)
            self.logger.info("Session elevated to enable mode")

    def run_command(self, command: str, elevated: bool = False) -> str:
        if self.session:
            if elevated:
                self.enable()
                self.session.write(f"{command}\n".encode())
                response = self.session.read_until(b"OsmoHLR# ").decode().replace(command, "").replace("OsmoHLR# ", "").strip()
            else:
                self.session.write(f"{command}\n".encode())
                response = self.session.read_until(b"OsmoHLR> ").decode().replace(command, "").replace("OsmoHLR> ", "").strip()
            self.logger.info(f"Command:\n{command}\n\nResponse:\n{response}\n")
            return response
        else:
            raise Exception("Session is not connected")

    def run_multiple_commands(self, commands: list, elevated: bool = False) -> list:
        responses = []
        for command in commands:
            responses.append(self.run_command(command, elevated))
        return responses

    def get_session_log(self):
        with open("osmo_hlr.log", "r") as log_file:
            return log_file.read()


def osmo_hlr_run_single(command: str):
    """Run a standard command on the Osmocom HLR VTY interface."""
    osmohlr = OsmocomHLR("localhost", 4258)
    osmohlr.connect()
    response = osmohlr.run_command(command, elevated=False)
    osmohlr.disconnect()
    return response


def osmo_hlr_run_single_elevated(command: str):
    """Run an elevated command on the Osmocom HLR VTY interface."""
    osmohlr = OsmocomHLR("localhost", 4258)
    osmohlr.connect()
    response = osmohlr.run_command(command, elevated=True)
    osmohlr.disconnect()
    return response


def osmo_hlr_run_multiple(commands: list[str]) -> list[str]:
    """Run a standard command on the Osmocom HLR VTY interface."""
    osmohlr = OsmocomHLR("localhost", 4258)
    osmohlr.connect()
    response = osmohlr.run_multiple_commands(commands, elevated=False)
    osmohlr.disconnect()
    return response


def osmo_hlr_run_multiple_elevated(commands: list[str]) -> list[str]:
    """Run an elevated command on the Osmocom HLR VTY interface."""
    osmohlr = OsmocomHLR("localhost", 4258)
    osmohlr.connect()
    response = osmohlr.run_multiple_commands(commands, elevated=True)
    osmohlr.disconnect()
    return response


class OsmocomMSC:
    def __init__(self, host: Union[IPv4Address, IPv6Address, str], port: int):
        self.host = host
        self.port = port
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("osmo_msc.log")
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def connect(self):
        self.session = Telnet(str(self.host), self.port)
        self.session.read_until(b"OsmoMSC> ", timeout=5)
        self.logger.info(f"Connected to {self.host}:{self.port}")

    def disconnect(self):
        if self.session:
            self.session.close()
            self.logger.info(f"Disconnected from {self.host}:{self.port}")

    def enable(self):
        if self.session:
            self.session.write(b"enable\n")
            self.session.read_until(b"OsmoMSC# ", timeout=5)
            self.logger.info("Session elevated to enable mode")

    def run_command(self, command: str, elevated: bool = False) -> str:
        if self.session:
            if elevated:
                self.enable()
                self.session.write(f"{command}\n".encode())
                response = self.session.read_until(b"OsmoMSC# ").decode().replace(command, "").replace("OsmoMSC# ", "").strip()
            else:
                self.session.write(f"{command}\n".encode())
                response = self.session.read_until(b"OsmoMSC> ").decode().replace(command, "").replace("OsmoMSC> ", "").strip()
            self.logger.info(f"Command:\n{command}\n\nResponse:\n{response}\n")
            return response
        else:
            raise Exception("Session is not connected")

    def run_multiple_commands(self, commands: list, elevated: bool = False) -> list:
        responses = []
        for command in commands:
            responses.append(self.run_command(command, elevated))
        return responses

    def get_session_log(self):
        with open("osmo_msc.log", "r") as log_file:
            return log_file.read()


def osmo_msc_run_single(command: str):
    """Run a standard command on the Osmocom MSC VTY interface."""
    osmomsc = OsmocomMSC("localhost", 4254)
    osmomsc.connect()
    response = osmomsc.run_command(command, elevated=False)
    osmomsc.disconnect()
    return response


def osmo_msc_run_single_elevated(command: str):
    """Run an elevated command on the Osmocom MSC VTY interface."""
    osmomsc = OsmocomMSC("localhost", 4254)
    osmomsc.connect()
    response = osmomsc.run_command(command, elevated=True)
    osmomsc.disconnect()
    return response


def osmo_msc_run_multiple(commands: list[str]) -> list[str]:
    """Run a standard command on the Osmocom MSC VTY interface."""
    osmomsc = OsmocomMSC("localhost", 4254)
    osmomsc.connect()
    response = osmomsc.run_multiple_commands(commands, elevated=False)
    osmomsc.disconnect()
    return response


def osmo_msc_run_multiple_elevated(commands: list[str]) -> list[str]:
    """Run an elevated command on the Osmocom MSC VTY interface."""
    osmomsc = OsmocomMSC("localhost", 4254)
    osmomsc.connect()
    response = osmomsc.run_multiple_commands(commands, elevated=True)
    osmomsc.disconnect()
    return response


def send_sms(recipient: SubscriberId, sender: SubscriberId, message: str):
    """
    ### subscriber(msisdn|extension|imsi|tmsi|id) ID sms sender(msisdn|extension|imsi|tmsi|id) SENDER_ID send LINE
    # % No subscriber found for msisdn 9990000
    """
    cmd = f"subscriber {recipient} sms sender {sender} send {message}"
    return osmo_msc_run_single_elevated(cmd)
