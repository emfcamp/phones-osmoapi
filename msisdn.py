import sqlite3


def get_msisdn_by_imsi(imsi: int):
    try:
        # Connect to the database
        conn = sqlite3.connect("hlr.db")
        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Get the MSISDN from IMSI in the database
        msisdn = cursor.execute("select msisdn from subscriber where imsi = ?", (imsi,)).fetchall()[0][0]

        # Writing the changes to the database
        conn.commit()
        # Close the cursor
        cursor.close()
        # Close the connection
        conn.close()
        return {"imsi": imsi, "msisdn": int(msisdn)}
    except Exception as e:
        raise (e)


def set_msisdn_by_imsi(imsi: int, new_msisdn: int):
    try:
        # Connect to the database
        conn = sqlite3.connect("hlr.db")
        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Check if the new MSISDN already exists in the database
        if cursor.execute("select msisdn from subscriber where msisdn = ?", (new_msisdn,)).fetchall():
            raise ValueError("MSISDN already exists in the database, please choose another MSISDN.")

        # Set the MSISDN in the database from the specified IMSI
        cursor.execute("update subscriber set msisdn = ? where imsi = ?", (new_msisdn, imsi)).fetchall()

        # Writing the changes to the database
        conn.commit()
        # Close the cursor
        cursor.close()
        # Close the connection
        conn.close()
        return {"imsi": imsi, "msisdn": int(new_msisdn)}
    except Exception as e:
        raise (e)


def set_default_msisdn(imsi: int, type: int, prefix: int = 904):
    try:
        return set_msisdn_by_imsi(imsi, new_msisdn=(generate_default_msisdn(imsi, type, prefix)))
    except Exception as e:
        raise (e)


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
