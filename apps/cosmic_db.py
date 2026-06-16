import yaml
import psycopg2

DBCFG = "/opt/pimes/config/db.yaml"

def get_conn():

    with open(DBCFG) as f:
        db = yaml.safe_load(f)

    return psycopg2.connect(
        host=db["host"],
        database=db["database"],
        user=db["user"],
        password=db["password"]
    )


def save_indices(kp, dst, obs_time, source):

    conn = get_conn()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO cosmic_indices
            (
                obs_time,
                kp,
                dst,
                source
            )
            VALUES
            (
                %s,%s,%s,%s
            )
            """,
            (
                obs_time,
                kp,
                dst,
                source
            )
        )

        conn.commit()

    finally:

        conn.close()
