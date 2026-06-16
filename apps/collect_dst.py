#!/usr/bin/env python3

import re
import yaml
import psycopg2
import requests
from datetime import datetime

URL = (
    "https://wdc.kugi.kyoto-u.ac.jp/"
    "dst_realtime/presentmonth/index.html"
)

DBCFG = "/opt/pimes/config/db.yaml"


def get_db():

    with open(DBCFG) as f:
        cfg = yaml.safe_load(f)

    return psycopg2.connect(
        host=cfg["host"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"]
    )


def fetch_dst():

    html = requests.get(
        URL,
        timeout=60
    ).text

    today = datetime.utcnow().day

    pattern = rf"\n\s*{today}\s+(.*)"

    m = re.search(
        pattern,
        html
    )

    if not m:
        raise RuntimeError(
            f"Day {today} not found"
        )

    row = m.group(1)

    vals = []

    for tok in row.split():

        try:
            v = int(tok)

            if abs(v) < 1000:
                vals.append(v)

        except:
            pass

    if not vals:
        raise RuntimeError(
            "No valid Dst values"
        )

    return float(vals[-1])


def save_dst(dst):

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO cosmic_indices
            (
                obs_time,
                kp,
                dst,
                source
            )
            VALUES
            (
                NOW(),
                NULL,
                %s,
                'KYOTO_DST'
            )
            """,
            (dst,)
        )

        conn.commit()

    finally:

        conn.close()


def main():

    dst = fetch_dst()

    print(
        f"DST = {dst}"
    )

    save_dst(dst)

    print(
        "Inserted into cosmic_indices"
    )


if __name__ == "__main__":
    main()
