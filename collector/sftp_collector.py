import yaml
import paramiko
from pathlib import Path

CONFIG_FILE = "/opt/pimes/config/bmkg_sftp.yaml"

with open(CONFIG_FILE) as f:
    cfg = yaml.safe_load(f)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    hostname=cfg["host"],
    port=cfg["port"],
    username=cfg["username"],
    password=cfg["password"]
)

sftp = ssh.open_sftp()

print("CONNECTED")

sftp.close()
ssh.close()
