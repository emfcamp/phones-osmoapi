from csv import DictReader
from pprint import pprint

from .osmo import osmo_hlr_run_single_elevated


def get_all_default_msisdn():
    """Get all default MSISDNs"""
    try:
        default_msisdns = []
        with open("data/default_msisdn_by_imsi.csv", newline="") as csvfile:
            reader = DictReader(csvfile)
            if "IMSI" not in reader.fieldnames or "DefaultMSISDN" not in reader.fieldnames:
                raise Exception("Invalid CSV header: missing IMSI or DefaultMSISDN")
            for row in reader:
                default_msisdns.append({"imsi": int(row["IMSI"]), "default_msisdn": int(row["DefaultMSISDN"])})
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
            if row["imsi"] == imsi:
                return int(row["default_msisdn"])
        raise ValueError("Unknown IMSI")
    except Exception as e:
        raise e


def get_all_subscribers_from_hlr():
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
            if line.startswith(" "):
                continue
            if len(line) < 1:
                continue
            row = line.split()
            sub_id = row[0]
            msisdn = row[1]
            imsi = row[2]
            imei = row[3]
            ## If msisdn hasn't been set, set it to -1
            if msisdn == "none": msisdn = -1
            ## If imei hasn't been set set to -1
            if "--------" in imei: imei = -1
            msisdns.append({"id": int(sub_id) ,"imsi": int(imsi), "msisdn": int(msisdn), "imei": int(imei)})
        return msisdns
    except Exception as e:
        raise e
