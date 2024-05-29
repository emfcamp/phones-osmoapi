from asyncio import start_server
from csv import DictReader
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


def get_all_default_msisdn():
    """Get all default MSISDNs"""
    try:
        default_msisdns = []
        with open("default_msisdn_by_imsi.csv", newline='') as csvfile:
            reader = DictReader(csvfile)
            if "IMSI" not in reader.fieldnames or "DefaultMSISDN" not in reader.fieldnames:
                raise Exception("Invalid CSV header: missing IMSI or DefaultMSISDN")
            for row in reader:
                default_msisdns.append({"imsi": int(row['IMSI']), "default_msisdn": int(row['DefaultMSISDN'])})
        return default_msisdns
    except Exception as e:
        raise e


def get_default_msisdn_by_imsi(imsi: int):
    """Get the default MSISDN for a given IMSI

    Parameters
    ----------
    imsi : int, required
        The IMSI of the SIM card
    """
    try:
        default_msisdns = get_all_default_msisdn()
        for row in default_msisdns:
            if row['imsi'] == imsi:
                return int(row['default_msisdn'])
        raise ValueError("Unknown IMSI")
    except Exception as e:
        raise e


def reset_msisdn_by_imsi_to_default(imsi: int):
    """Resets the MSISDN for a given IMSI to the default MSISDN

    Parameters
    ----------
    imsi : int, required
        The IMSI of the SIM card
    """
    try:
        default_msisdn = get_default_msisdn_by_imsi(imsi)
        return set_msisdn_by_imsi(imsi, default_msisdn)
    except Exception as e:
        raise e


def get_all_msisdn_from_hlr():
    """Get all MSISDNs"""
    """
    OsmoHLR# show subscribers all
ID     MSISDN        IMSI              IMEI              NAM
-----  ------------  ----------------  ----------------  -----
1      90422263      999420000002263    -------------    CSPS
    """
    try:
        re = osmo_hlr_run_single_elevated("show subscribers all")
        lines = re.splitlines()
        msisdns = []
        for line in lines:
            if "Error" in line:
                raise ValueError(line)
            if "ID" in line:
                continue
            if line.startswith("-----"):
                continue
            if len(line) < 1:
                continue
            msisdn = line.split()[1]
            imsi = line.split()[2]
            msisdns.append({"imsi": int(imsi), "msisdn": int(msisdn)})
        return msisdns
    except Exception as e:
        raise e


#def generate_default_msisdn(imsi: int, prefix: int) -> int:
#    """Generates a default MSISDN based on the IMSI, type and prefix
#
#    Parameters
#    ----------
#    imsi : int, required
#        The IMSI of the SIM card
#    prefix : int, required
#        Network Defined Prefix for SIM cards
#        e.g. 901 for DECT, ..., 904 for SIMs
#
#    Returns
#    -------
#    int
#        Generated MSISDN
#
#    Raises
#    ------
#    ValueError
#        If the type is not 1, 2 or 3 or 4
#    """
#
#    if len(str(imsi)) < 15:
#        raise ValueError("Invalid IMSI - IMSI must be 15 digits long")
#    else:
#        if str(imsi).startswith("901700500"): # EMF IMSI Range - pSIM
#            type = 1
#            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
#        elif str(imsi).startswith("901700501"): # EMF IMSI Range - eSIM
#            type = 2
#            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
#        elif str(imsi).startswith("901700502"): # EMF IMSI Range - custom SIM
#            type = 3
#            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
#        elif str(imsi).startswith("99942"): # new c3gsm SIM Range
#            type = 4
#            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
#        elif str(imsi).startswith("26242"): # old c3gsm SIM Range
#            type = 5
#            return int(str(str(prefix) + str(type) + str(imsi)[-6:]))
#        elif str(imsi).startswith("901700000"): # c3gsm existing 90170 IMSI Range
#            type = 6
#            return int(str(str(prefix) + str(type) + str(imsi)[-4:]))
#        else:
#            raise ValueError("Invalid IMSI presented. Please ensure the IMSI is correct and valid within the event network specification.")
