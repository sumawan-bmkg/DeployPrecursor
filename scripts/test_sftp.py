import os
import stat
import paramiko

HOST = "202.90.198.224"
PORT = 4343
USER = "precursor"
PASSWORD = "otomatismon"

REMOTE_DIR = "/home/precursor/SEISMO/DATA/SCN/Nowrec"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy()
)

ssh.connect(
    HOST,
    port=PORT,
    username=USER,
    password=PASSWORD,
    timeout=30
)

sftp = ssh.open_sftp()

files = []

for f in sftp.listdir_attr(REMOTE_DIR):

    if stat.S_ISREG(f.st_mode):
        files.append(
            (
                f.filename,
                f.st_size,
                f.st_mtime
            )
        )

files = sorted(
    files,
    key=lambda x: x[2]
)

for row in files[-10:]:
    print(row)

sftp.close()
ssh.close()
