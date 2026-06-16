#!/usr/bin/env python3

import os
import yaml
import psycopg2

from pathlib import Path

from run_station import (
    load_model,
    build_tensor_from_scn,
    run_inference,
    save_prediction
)

RAW_ROOT = "/opt/pimes/data/raw"
DBCFG = "/opt/pimes/config/db.yaml"


# ==================================================
# DATABASE
# ==================================================

def get_db():

    with open(DBCFG) as f:
        cfg = yaml.safe_load(f)

    return psycopg2.connect(
        host=cfg["host"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"]
    )


# ==================================================
# COSMIC INDEX
# ==================================================

def get_latest_cosmic():

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT kp
            FROM cosmic_indices
            WHERE kp IS NOT NULL
            ORDER BY obs_time DESC
            LIMIT 1
            """
        )

        row = cur.fetchone()

        kp = float(row[0]) if row else 0.0

        cur.execute(
            """
            SELECT dst
            FROM cosmic_indices
            WHERE dst IS NOT NULL
            ORDER BY obs_time DESC
            LIMIT 1
            """
        )

        row = cur.fetchone()

        dst = float(row[0]) if row else 0.0

        return kp, dst

    finally:

        conn.close()


# ==================================================
# PROCESS ONE STATION
# ==================================================

def process_station(
    model,
    station_code,
    kp,
    dst
):

    station_dir = Path(RAW_ROOT) / station_code

    if not station_dir.exists():

        print(
            f"[SKIP] {station_code}: directory missing"
        )

        return

    files = sorted(
        station_dir.glob("*")
    )

    if not files:

        print(
            f"[SKIP] {station_code}: no file"
        )

        return

    latest = files[-1]

    if latest.stat().st_size < 1000:

        print(
            f"[SKIP] {station_code}: empty file"
        )

        return

    print(
        f"[RUN] {station_code} -> {latest.name}"
    )

    tensor = build_tensor_from_scn(
        str(latest),
        station_code
    )

    result = run_inference(
    model,
    tensor,
    kp,
    dst
    )

    print(
        f"[RESULT] "
        f"P={result['probability']:.4f} "
        f"M={result['magnitude_class']} "
        f"AZ={result['azimuth']:.1f}"
    )

    save_prediction(
        station_code=station_code,
        probability=result["probability"],
        magnitude_class=result["magnitude_class"],
        azimuth=result["azimuth"],
        kp=kp,
        dst=dst
    )


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "\n====================================="
    )
    print(
        "PIMES MULTI-STATION INFERENCE"
    )
    print(
        "=====================================\n"
    )

    kp, dst = get_latest_cosmic()

    print(
        f"[COSMIC] kp={kp} dst={dst}"
    )

    print(
        "\n[MODEL] Loading..."
    )

    model = load_model()

    print(
        "[MODEL] Ready"
    )

    stations = []

    for d in sorted(
        os.listdir(RAW_ROOT)
    ):

        full = Path(RAW_ROOT) / d

        if not full.is_dir():
            continue

        if d in (
            "archive",
            "incoming"
        ):
            continue

        stations.append(d)

    print(
        f"\n[INFO] {len(stations)} stations found\n"
    )

    success = 0
    failed = 0

    for station in stations:

        try:

            process_station(
                model,
                station,
                kp,
                dst
            )

            success += 1

        except Exception as e:

            print(
                f"[ERROR] {station}: {e}"
            )

            failed += 1

    print(
        "\n====================================="
    )
    print(
        "RUN FINISHED"
    )
    print(
        "====================================="
    )

    print(
        f"SUCCESS : {success}"
    )

    print(
        f"FAILED  : {failed}"
    )

    print(
        "=====================================\n"
    )


if __name__ == "__main__":
    main()
