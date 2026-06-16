#!/usr/bin/env python3

import os
import gzip
import struct
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ============================================================
# STATION BASELINES
# ============================================================

STATION_BASELINES = {
    'GTO': {'H': 40000, 'Z': 30000},
    'GSI': {'H': 40000, 'Z': 30000},
    'ALR': {'H': 38000, 'Z': 32000},
    'AMB': {'H': 38000, 'Z': 32000},
    'BTN': {'H': 38000, 'Z': 32000},
    'CLP': {'H': 38000, 'Z': 32000},
    'TND': {'H': 40000, 'Z': 30000},
    'SCN': {'H': 38000, 'Z': 32000},
    'MLB': {'H': 38000, 'Z': 32000},
    'SBG': {'H': 38000, 'Z': 32000},
    'YOG': {'H': 38000, 'Z': 32000},
    'MJB': {'H': 38000, 'Z': 32000},
    'LWK': {'H': 38000, 'Z': 32000},
    'SMG': {'H': 38000, 'Z': 32000},
    'SKB': {'H': 38000, 'Z': 32000},
    'TRT': {'H': 38000, 'Z': 32000},
    'PLU': {'H': 38000, 'Z': 32000},
    'LWA': {'H': 38000, 'Z': 32000},
    'KPY': {'H': 38000, 'Z': 32000},
    'LPS': {'H': 38000, 'Z': 32000},
    'SRG': {'H': 38000, 'Z': 32000},
    'LUT': {'H': 38000, 'Z': 32000},
    'SMI': {'H': 38000, 'Z': 32000},
    'TNT': {'H': 38000, 'Z': 32000},
}


class SCNParser:

    def __init__(self):
        logger.info("SCNParser initialized")

    # ============================================================
    # PUBLIC
    # ============================================================

    def parse_scn_file(self, filepath, station):

        num_seconds = 86400

        nan_result = {
            "H": np.full(num_seconds, np.nan, dtype=np.float32),
            "D": np.full(num_seconds, np.nan, dtype=np.float32),
            "Z": np.full(num_seconds, np.nan, dtype=np.float32),
        }

        if not os.path.exists(filepath):

            logger.error(
                f"File not found: {filepath}"
            )

            return nan_result

        try:

            filesize = os.path.getsize(filepath)

            if filesize == 0:

                logger.warning(
                    f"Empty file: {filepath}"
                )

                return nan_result

            # --------------------------------------------------
            # GZIP FORMAT
            # --------------------------------------------------

            if filepath.endswith(".gz"):

                with gzip.open(
                    filepath,
                    "rb"
                ) as f:

                    binary_data = f.read()

            # --------------------------------------------------
            # RAW FORMAT
            # --------------------------------------------------

            else:

                with open(
                    filepath,
                    "rb"
                ) as f:

                    binary_data = f.read()

            if len(binary_data) == 0:

                logger.warning(
                    f"No binary content: {filepath}"
                )

                return nan_result

            return self._parse_binary_data(
                binary_data,
                station
            )

        except Exception as e:

            logger.exception(
                f"Error parsing {filepath}: {e}"
            )

            return nan_result

    # ============================================================
    # INTERNAL PARSER
    # ============================================================

    def _parse_binary_data(
        self,
        binary_data,
        station
    ):

        num_seconds = 86400

        header_size = 32
        record_size = 17

        baseline = STATION_BASELINES.get(
            station,
            {"H": 40000, "Z": 30000}
        )

        h_data = np.full(
            num_seconds,
            np.nan,
            dtype=np.float32
        )

        d_data = np.full(
            num_seconds,
            np.nan,
            dtype=np.float32
        )

        z_data = np.full(
            num_seconds,
            np.nan,
            dtype=np.float32
        )

        if len(binary_data) <= header_size:

            logger.warning(
                "Binary file shorter than header"
            )

            return {
                "H": h_data,
                "D": d_data,
                "Z": z_data,
            }

        data_start = binary_data[
            header_size:
        ]

        max_records = min(
            num_seconds,
            len(data_start) // record_size
        )

        logger.info(
            f"{station}: records={max_records}"
        )

        for i in range(max_records):

            offset = i * record_size

            record = data_start[
                offset:
                offset + record_size
            ]

            if len(record) < record_size:
                break

            try:

                h_dev = (
                    struct.unpack(
                        "<h",
                        record[0:2]
                    )[0]
                    * 0.1
                )

                d_dev = (
                    struct.unpack(
                        "<h",
                        record[2:4]
                    )[0]
                    * 0.1
                )

                z_dev = (
                    struct.unpack(
                        "<h",
                        record[4:6]
                    )[0]
                    * 0.1
                )

                h_data[i] = (
                    baseline["H"]
                    + h_dev
                )

                d_data[i] = d_dev

                z_data[i] = (
                    baseline["Z"]
                    + z_dev
                )

            except Exception:
                continue

        return {
            "H": h_data,
            "D": d_data,
            "Z": z_data,
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    parser = SCNParser()

    print(
        "SCNParser ready."
    )
