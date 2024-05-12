from re import L
from osmo import osmo_hlr_run_single_elevated 
from pprint import pprint


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
        re = osmo_hlr_run_single_elevated(
            f"subscriber imsi {imsi} update msisdn {new_msisdn}"
        )
        lines = re.splitlines()
        for line in lines:
            pprint(line)
            if "Error" in line:
                raise ValueError(line)
            if "Updated " in line:
                return {"imsi": imsi, "msisdn": new_msisdn}
    except Exception as e:
        raise e


def set_default_msisdn(imsi: int, type: int, prefix: int = 904):
    """Set the default MSISDN for a given IMSI"""
    try:
        default_msisdn = generate_default_msisdn(imsi, type, prefix)
        re = osmo_hlr_run_single_elevated(
            f"subscriber imsi {imsi} update msisdn {default_msisdn}"
        )
        lines = re.splitlines()
        for line in lines:
            if "Error" in line:
                raise ValueError(line)
            if "Updated " in line:
                return {"imsi": imsi, "msisdn": default_msisdn}
    except Exception as e:
        raise e


def generate_default_msisdn(imsi: int, type: int, prefix: int) -> int:
    """Generates a default MSISDN based on the IMSI, type and prefix

    Parameters
    ----------
    imsi : int, required
        The IMSI of the SIM card
    type : int, required
        The type of SIM being added
        1. Original pSIM
        2. New pSIM
        3. c3camp23 eSIM
        4. EMF2024 eSIM
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
    if type == 1:
        return int(str(str(prefix) + str(type) + str(imsi)[-5:]))
    elif type == 2:
        return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
    elif type == 3:
        return int(str(str(prefix) + str(type) + str(imsi)[-3:]))
    elif type == 4:
        return int(str(str(prefix) + str(type) + str(imsi)[-2:]))
    else:
        raise ValueError("Invalid type")
