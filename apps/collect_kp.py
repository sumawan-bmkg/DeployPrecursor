#!/usr/bin/env python3

import yaml
import psycopg2
import requests

from datetime import datetime

DBCFG = "/opt/pimes/config/db.yaml"

URL = (
    "https://services.swpc.noaa.gov/json/"
    "planetary_k_index_1m.json"
)


def get_db():

    with open(DBCFG) as f:
        db = yaml.safe_load(f)

    return psycopg2.connect(
        host=db["host"],
        database=db["database"],
        user=db["user"],
        password=db["password"]
    )


def fetch_latest_kp():

    r = requests.get(
        URL,
        timeout=60
    )

    r.raise_for_status()

    data = r.json()

    if not data:
        raise RuntimeError(
            "NOAA returned empty dataset"
        )

    row = data[-1]

    obs_time = datetime.fromisoformat(
        row["time_tag"]
    )

    kp = float(
        row["kp_index"]
    )

    return obs_time, kp


def save_kp(
    obs_time,
    kp
):

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO cosmic_indices
            (
                obs_time,
                kp,
                source
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                obs_time,
                kp,
                "NOAA_KP"
            )
        )

        conn.commit()

    finally:

        conn.close()


def main():

    obs_time, kp = (
        fetch_latest_kp()
    )

    print(
        f"KP={kp} "
        f"TIME={obs_time}"
    )

    save_kp(
        obs_time,
        kp
    )

    print(
        "INSERT OK"
    )


if __name__ == "__main__":
    main()
