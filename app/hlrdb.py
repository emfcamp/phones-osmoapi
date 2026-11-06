import sqlite3
from pathlib import Path

from .config import settings

# enum osmo_auth_algo from libosmocore (stored as algo_id_2g / algo_id_3g)
AUTH_ALGO = {
    0: "none",
    1: "comp128v1",
    2: "comp128v2",
    3: "comp128v3",
    4: "xor-3g",
    5: "milenage",
    6: "xor-2g",
    7: "tuak",
}

QUERY = """
SELECT s.id, s.imsi, s.msisdn, s.imei,
       s.nam_cs, s.nam_ps, s.ms_purged_cs, s.ms_purged_ps,
       s.vlr_number, s.sgsn_number,
       s.last_lu_seen, s.last_lu_seen_ps,
       a2.algo_id_2g, a2.ki,
       a3.algo_id_3g, a3.k, a3.op, a3.opc, a3.sqn, a3.ind_bitlen
FROM subscriber s
LEFT JOIN auc_2g a2 ON a2.subscriber_id = s.id
LEFT JOIN auc_3g a3 ON a3.subscriber_id = s.id
ORDER BY s.id
"""


class HlrDbUnavailable(Exception):
    """The HLR database file is missing or can't be read."""


def _algo_name(algo_id: int | None) -> str | None:
    if algo_id is None:
        return None
    return AUTH_ALGO.get(algo_id, f"unknown({algo_id})")


KEY_FIELDS = ("ki", "k", "op", "opc", "ind_bitlen")


def list_subscribers(db_path: str | Path | None = None, include_keys: bool = False) -> list[dict]:
    """Return every subscriber in the HLR database."""
    path = Path(db_path or settings.hlr_db_path)
    if not path.is_file():
        raise HlrDbUnavailable(f"HLR database not found at {path}")

    try:
        # mode=ro, writes should be done via CTRL interface
        conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=5)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(QUERY).fetchall()
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise HlrDbUnavailable(f"Couldn't read HLR database at {path}: {e}") from e

    return [_to_dict(r, include_keys) for r in rows]


def _to_dict(r: sqlite3.Row, include_keys: bool) -> dict:
    sub = {
        "id": r["id"],
        "imsi": r["imsi"],
        "msisdn": r["msisdn"] or None,
        "imei": r["imei"] or None,
        "cs_enabled": bool(r["nam_cs"]),
        "ps_enabled": bool(r["nam_ps"]),
        "purged_cs": bool(r["ms_purged_cs"]),
        "purged_ps": bool(r["ms_purged_ps"]),
        "vlr_number": r["vlr_number"] or None,
        "sgsn_number": r["sgsn_number"] or None,
        "last_lu_seen_cs": r["last_lu_seen"] or None,
        "last_lu_seen_ps": r["last_lu_seen_ps"] or None,
        "auth_2g": _algo_name(r["algo_id_2g"]),
        "auth_3g": _algo_name(r["algo_id_3g"]),
        "sqn": r["sqn"],
    }
    if include_keys:
        sub.update({f: r[f] for f in KEY_FIELDS})
    return sub
