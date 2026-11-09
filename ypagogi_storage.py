import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ypagogi_cases.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ypagogi_cases (
                case_id TEXT PRIMARY KEY,
                history TEXT NOT NULL,
                data TEXT NOT NULL,
                round_number INTEGER NOT NULL
            )
        """)


def save_case(case_id, history, data, round_number):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO ypagogi_cases
                (case_id, history, data, round_number)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                history = excluded.history,
                data = excluded.data,
                round_number = excluded.round_number
        """, (
            case_id,
            json.dumps(history, ensure_ascii=False),
            json.dumps(data, ensure_ascii=False),
            round_number
        ))


def load_case(case_id):
    if not case_id:
        return None

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT * FROM ypagogi_cases
            WHERE case_id = ?
        """, (case_id,)).fetchone()

    if row is None:
        return None

    return {
        "history": json.loads(row["history"]),
        "data": json.loads(row["data"]),
        "round_number": row["round_number"]
    }
