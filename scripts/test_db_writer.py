from datetime import datetime
import sys

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts"
)

from database.db_writer_v2 import DatabaseWriter


cfg = {
    "host": "localhost",
    "port": 5432,
    "database": "pimes",
    "user": "pimesuser",
    "password": "Precursor@2026!"
}

writer = DatabaseWriter(cfg)

pred_id = writer.insert_prediction(
    station_code="SCN",
    prediction_time=datetime.utcnow(),
    probability=0.3683,
    magnitude_class=4,
    azimuth_class=109,
    kp=2.0,
    dst=-10.0,
    model_version="v3_v8_smoketest"
)

print("PREDICTION_ID =", pred_id)

rows = writer.get_recent_predictions(
    hours=24,
    limit=5
)

print("\nLAST RECORDS:")
for r in rows:
    print(r)

writer.close()

print("\nDATABASE_PIPELINE_OK")
