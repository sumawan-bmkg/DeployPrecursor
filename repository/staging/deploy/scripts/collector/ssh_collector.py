#!/usr/bin/env python3

import paramiko

HOST = "202.90.198.224"
PORT = 4343
USER = "precursor"
PASSWORD = "otomatismon"

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

stdin, stdout, stderr = ssh.exec_command(
    "hostname"
)

print(stdout.read().decode())

ssh.close()
