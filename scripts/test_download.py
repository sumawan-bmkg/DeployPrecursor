import paramiko

HOST="202.90.198.224"
PORT=4343
USER="precursor"
PASSWORD="otomatismon"

REMOTE = (
    "/home/precursor/SEISMO/DATA/SCN/Nowrec/S260612.SCN"
)

LOCAL = "/tmp/S260612.SCN"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(
    paramiko.AutoAddPolicy()
)

ssh.connect(
    HOST,
    port=PORT,
    username=USER,
    password=PASSWORD
)

sftp = ssh.open_sftp()

sftp.get(REMOTE, LOCAL)

sftp.close()
ssh.close()

print("DOWNLOAD_OK")
