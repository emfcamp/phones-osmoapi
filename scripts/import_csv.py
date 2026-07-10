from csv import DictReader

import httpx


headers = {
    "Cookie": "emftel-session="
}
sim_endpoint = "https://phones.emfcamp.org/admin/sims"


records = []
with open("list.csv", newline="") as f:
    reader = DictReader(f)
    for row in reader:
        records.append({
            "imsi": row["IMSI"],
            "iccid": row["ICCID"],
            "ki": row["KI"],
            "opc": row["OPC"],
            "name": f"{row["owner"]}'s SIM",
            "gprsEnabled": "true"
        })


def add_sub(payload: dict):
    with httpx.Client(timeout=3) as client:
        resp = client.request("POST", sim_endpoint, headers=headers, data=payload)
        if resp.status_code != 200:
            print(resp.status_code)


for row in records:
    add_sub(row)
    input()
