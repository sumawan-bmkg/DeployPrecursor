#!/usr/bin/env python3

import os
import yaml
import paramiko
from pathlib import Path
from datetime import datetime, timedelta

import psycopg2


class SSHCollector:

    def __init__(self, cfg):

        self.cfg = cfg

        self.ssh_cfg = cfg["ssh"]
        self.db_cfg = cfg["database"]

        self.raw_dir = Path(
            cfg["storage"]["raw_dir"]
        )

        self.raw_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def get_db(self):

        return psycopg2.connect(
            host=self.db_cfg["host"],
            port=self.db_cfg["port"],
            database=self.db_cfg["database"],
            user=self.db_cfg["user"],
            password=self.db_cfg["password"]
        )

    def get_stations(self):

        conn = self.get_db()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT station_code
                    FROM stations
                    WHERE active=TRUE
                    ORDER BY station_code
                """)

                return [
                    r[0]
                    for r in cur.fetchall()
                ]

        finally:
            conn.close()

    def connect(self):

        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        ssh.connect(
            self.ssh_cfg["host"],
            port=self.ssh_cfg["port"],
            username=self.ssh_cfg["username"],
            password=self.ssh_cfg["password"],
            timeout=30
        )

        return ssh

    def remote_exists(self, sftp, remote_path):

        try:
            sftp.stat(remote_path)
            return True
        except:
            return False

    def save_raw_file(
        self,
        station,
        file_date,
        local_path,
        file_size
    ):

        conn = self.get_db()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO raw_files
                    (
                        station_code,
                        file_date,
                        file_path,
                        file_size
                    )
                    VALUES
                    (
                        %s,%s,%s,%s
                    )
                    """,
                    (
                        station,
                        file_date,
                        str(local_path),
                        file_size
                    )
                )

            conn.commit()

        finally:
            conn.close()

    def collect_date(self, target_date):

        yy = target_date.year % 100
        mm = target_date.month
        dd = target_date.day

        ssh = self.connect()
        sftp = ssh.open_sftp()

        stations = self.get_stations()

        success = 0

        for station in stations:

            filename = (
                f"S{yy:02d}{mm:02d}{dd:02d}.{station}"
            )

            remote_path = (
                f"/home/precursor/SEISMO/DATA/"
                f"{station}/Nowrec/{filename}"
            )

            if not self.remote_exists(
                sftp,
                remote_path
            ):
                print(
                    f"[SKIP] {station}"
                )
                continue

            station_dir = (
                self.raw_dir / station
            )

            station_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            local_path = (
                station_dir / filename
            )

            if not local_path.exists():

                print(
                    f"[DOWNLOAD] {filename}"
                )

                sftp.get(
                    remote_path,
                    str(local_path)
                )

            file_size = (
                local_path.stat().st_size
            )

            self.save_raw_file(
                station,
                target_date.date(),
                local_path,
                file_size
            )

            success += 1

        sftp.close()
        ssh.close()

        print(
            f"SUCCESS={success}"
        )


if __name__ == "__main__":

    with open(
        "/opt/pimes/config/collector.yaml"
    ) as f:

        cfg = yaml.safe_load(f)

    collector = SSHCollector(cfg)

    target = (
        datetime.utcnow()
        - timedelta(days=1)
    )

    collector.collect_date(target)
