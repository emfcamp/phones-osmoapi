from asyncio import start_server
from pprint import pprint
from re import L

from osmo import osmo_hlr_run_single_elevated


def get_msisdn_by_imsi(imsi: int):
    """Get the MSISDN for a given IMSI"""
    try:
        re = osmo_hlr_run_single_elevated(f"subscriber imsi {imsi} show")
        lines = re.splitlines()
        for line in lines:
            pprint(line)
            if "Error" in line:
                raise ValueError(line)
            if "MSISDN: " in line:
                return {"imsi": imsi, "msisdn": int(line.split(":")[1].strip())}
    except Exception as e:
        raise e


def set_msisdn_by_imsi(imsi: int, new_msisdn: int):
    """Set the MSISDN for a given IMSI"""
    try:
        re = osmo_hlr_run_single_elevated(f"subscriber imsi {imsi} update msisdn {new_msisdn}")
        lines = re.splitlines()
        for line in lines:
            pprint(line)
            if "Error" in line:
                raise ValueError(line)
            if "Updated " in line:
                return {"imsi": imsi, "msisdn": new_msisdn}
    except Exception as e:
        raise e


def set_default_msisdn(imsi: int, prefix: int = 904):
    """Set the default MSISDN for a given IMSI
    
    Parameters
    ----------
    imsi : int, required
        The IMSI of the SIM card
    prefix : int, optional, default: int(904)
        Network Defined Prefix for devices
        e.g. 904 for SIMs
    """
    try:
        default_msisdn = generate_default_msisdn(imsi, prefix)
        re = osmo_hlr_run_single_elevated(f"subscriber imsi {imsi} update msisdn {default_msisdn}")
        lines = re.splitlines()
        for line in lines:
            if "Error" in line:
                raise ValueError(line)
            if "Updated " in line:
                return {"imsi": imsi, "msisdn": default_msisdn}
    except Exception as e:
        raise e


def generate_default_msisdn(imsi: int, prefix: int) -> int:
    """Generates a default MSISDN based on the IMSI, type and prefix

    Parameters
    ----------
    imsi : int, required
        The IMSI of the SIM card
    prefix : int, required
        Network Defined Prefix for SIM cards
        e.g. 901 for DECT, ..., 904 for SIMs

    Returns
    -------
    int
        Generated MSISDN

    Raises
    ------
    ValueError
        If the type is not 1, 2 or 3 or 4
    """

    if len(str(imsi)) < 15:
        raise ValueError("Invalid IMSI - IMSI must be 15 digits long")
    else:
        if str(imsi).startswith("901700500"): # EMF IMSI Range - pSIM
            type = 1
            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
        elif str(imsi).startswith("901700501"): # EMF IMSI Range - eSIM
            type = 2
            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
        elif str(imsi).startswith("901700502"): # EMF IMSI Range - custom SIM
            type = 3
            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
        elif str(imsi).startswith("99942"): # new c3gsm SIM Range
            type = 4
            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
        elif str(imsi).startswith("26242"): # old c3gsm SIM Range
            type = 5
            return int(str(str(prefix) + str(type) + str(imsi)[-6:]))
        elif str(imsi).startswith("901700000"): # c3gsm existing 90170 IMSI Range
            type = 6
            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
        else:
            raise ValueError("Invalid IMSI presented. Please ensure the IMSI is correct and valid within the event network specification.")
