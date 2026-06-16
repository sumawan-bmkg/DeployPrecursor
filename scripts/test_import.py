import sys

sys.path.insert(
    0,
    "/opt/pimes/repository/staging/deploy/scripts/database"
)

from database.db_writer_v2 import DatabaseWriter

print("IMPORT_OK")
