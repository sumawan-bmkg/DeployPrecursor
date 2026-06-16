#!/usr/bin/env python3

import yaml
import psycopg2

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


def get_latest_cosmic():

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute("""
            SELECT kp
            FROM cosmic_indices
            WHERE kp IS NOT NULL
            ORDER BY obs_time DESC
            LIMIT 1
        """)

        kp_row = cur.fetchone()

        cur.execute("""
            SELECT dst
            FROM cosmic_indices
            WHERE dst IS NOT NULL
            ORDER BY obs_time DESC
            LIMIT 1
        """)

        dst_row = cur.fetchone()

        kp = float(kp_row[0]) if kp_row else 0.0
        dst = float(dst_row[0]) if dst_row else 0.0

        return {
            "kp": kp,
            "dst": dst
        }

    finally:

        conn.close()


print(get_latest_cosmic())
