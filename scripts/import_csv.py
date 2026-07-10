from csv import DictReader

import httpx
import time


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
            "name": "",
            "gprsEnabled": "false"
        })


def add_sub(payload: dict):
    with httpx.Client(timeout=3) as client:
        resp = client.request("POST", sim_endpoint, headers=headers, data=payload)
        if resp.status_code != 302:
            if "A SIM with that IMSI has already been onboarded" in resp.text:
                print(f"{payload["imsi"]} already imported :)")
                return

            print(resp.status_code)
            with open(f"{payload["imsi"]}.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
        print(f"Imported SIM {payload["imsi"]}")


for row in records:
    add_sub(row)
    time.sleep(1)
