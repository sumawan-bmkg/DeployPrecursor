from database.db_writer_v2 import DatabaseWriter

cfg = {
    "host": "localhost",
    "port": 5432,
    "database": "pimes",
    "user": "pimesuser",
    "password": "Precursor@2026!",
    "pool_size": 5
}

db = DatabaseWriter(cfg)

print("DB CONNECTION OK")
