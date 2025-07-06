# snowflake_db.py

import os
from dotenv import load_dotenv
import json
import snowflake.connector

# Load all environment vars from .env
load_dotenv()

ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT")
USER      = os.getenv("SNOWFLAKE_USER")
PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD")
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
DATABASE  = os.getenv("SNOWFLAKE_DATABASE")
SCHEMA    = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")

def get_connection():
    """Return a Snowflake connection using creds in .env."""
    return snowflake.connector.connect(
        account   = ACCOUNT,
        user      = USER,
        password  = PASSWORD,
        warehouse = WAREHOUSE,
        database  = DATABASE,
        schema    = SCHEMA,
    )

def initialize():
    """
    Create DATABASE, SCHEMA, and activity_logs table if they don’t exist.
    """
    ctx = get_connection()
    cs  = ctx.cursor()
    try:
        cs.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
        cs.execute(f"USE DATABASE {DATABASE}")
        cs.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        cs.execute(f"USE SCHEMA {SCHEMA}")
        cs.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
              id           INTEGER AUTOINCREMENT PRIMARY KEY,
              session_id   STRING,
              timestamp    TIMESTAMP_NTZ,
              duration     STRING,
              raw_summary  STRING,
              json_payload VARIANT,
              capture_mode STRING
            )
        """)
    finally:
        cs.close()
        ctx.close()

def insert_logs(parsed_entries: list[dict]):
    """
    Batch-insert parsed log entries. Each entry dict needs:
      - timestamp    (ISO str)
      - duration     (str)
      - capture_mode (str)
      - optionally session_id, raw_summary
      - all other data stored in the VARIANT column
    """
    initialize()
    ctx = get_connection()
    cs  = ctx.cursor()
    try:
        sql = """
        INSERT INTO activity_logs
          (session_id, timestamp, duration, raw_summary, json_payload, capture_mode)
        SELECT
          %(session_id)s,
          to_timestamp_ntz(%(timestamp)s),
          %(duration)s,
          %(raw_summary)s,
          PARSE_JSON(%(json_payload)s),
          %(capture_mode)s
        """

        # build params list
        params = []
        for e in parsed_entries:
            params.append({
                "session_id":   e.get("session_id"),
                "timestamp":    e.get("timestamp"),
                "duration":     e.get("duration"),
                "raw_summary":  e.get("raw_summary"),
                "json_payload": json.dumps(e),
                "capture_mode": e.get("capture_mode")
            })

        # execute one INSERT per entry (avoids multi-row rewrite issues)
        for p in params:
            cs.execute(sql, p)

        ctx.commit()
    finally:
        cs.close()
        ctx.close()
