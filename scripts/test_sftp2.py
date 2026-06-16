import paramiko

HOST="202.90.198.224"
PORT=4343
USER="precursor"
PASSWORD="otomatismon"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    HOST,
    port=PORT,
    username=USER,
    password=PASSWORD
)

stdin, stdout, stderr = ssh.exec_command(
    "ls -1 /home/precursor/SEISMO/DATA/SCN/Nowrec | tail -20"
)

print(stdout.read().decode(errors="replace"))

print(stderr.read().decode(errors="replace"))

ssh.close()
