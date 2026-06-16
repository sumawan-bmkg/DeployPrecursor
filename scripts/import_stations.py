import pandas as pd
import psycopg2

CSV_FILE = "/opt/pimes/config/stations.csv"

conn = psycopg2.connect(
    host="localhost",
    database="pimes",
    user="pimesuser",
    password="Precursor@2026!"
)

df = pd.read_csv(CSV_FILE)

cur = conn.cursor()

for _, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO stations
        (station_code, latitude, longitude)
        VALUES (%s,%s,%s)
        ON CONFLICT (station_code)
        DO NOTHING
        """,
        (
            row["station_code"],
            row["latitude"],
            row["longitude"]
        )
    )

conn.commit()

cur.close()
conn.close()

print(f"Imported {len(df)} stations")
