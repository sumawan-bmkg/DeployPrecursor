from pathlib import Path
import psycopg2
import yaml

print("=" * 60)
print("PIMES HEALTHCHECK")
print("=" * 60)

paths = [
    "/opt/pimes/config",
    "/opt/pimes/data",
    "/opt/pimes/logs",
    "/opt/pimes/checkpoints",
    "/opt/pimes/preprocessing",
]

print("\nFILESYSTEM")

for p in paths:
    status = "OK" if Path(p).exists() else "MISSING"
    print(f"{status:8} {p}")

print("\nDATABASE")

try:
    with open("/opt/pimes/config/db.yaml") as f:
        db = yaml.safe_load(f)

    conn = psycopg2.connect(
        host=db["host"],
        database=db["database"],
        user=db["user"],
        password=db["password"]
    )

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM stations")
    count = cur.fetchone()[0]

    print(f"OK       stations={count}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"ERROR    {e}")
