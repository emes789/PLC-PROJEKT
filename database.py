import sqlite3
import csv
import os
from datetime import datetime

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "machine_monitor.db")


class Database:
    def __init__(self, path: str = _DEFAULT_PATH):
        self.path = path
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS readings (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts        TEXT    NOT NULL,
                    param     TEXT    NOT NULL,
                    value     REAL    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS anomalies (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts        TEXT    NOT NULL,
                    param     TEXT    NOT NULL,
                    value     REAL    NOT NULL,
                    reason    TEXT    NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_anomalies_param
                    ON anomalies(param);
                """
            )

    def save_reading(self, timestamp: float, readings: dict[str, float]) -> None:
        ts = _fmt(timestamp)
        rows = [(ts, k, v) for k, v in readings.items()]
        with sqlite3.connect(self.path) as conn:
            conn.executemany(
                "INSERT INTO readings (ts, param, value) VALUES (?, ?, ?)", rows
            )

    def save_anomaly(
        self, timestamp: float, param: str, value: float, reason: str
    ) -> None:
        ts = _fmt(timestamp)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO anomalies (ts, param, value, reason) VALUES (?, ?, ?, ?)",
                (ts, param, value, reason),
            )

    def get_recent_anomalies(self, limit: int = 200) -> list[tuple]:
        with sqlite3.connect(self.path) as conn:
            return conn.execute(
                "SELECT ts, param, value, reason FROM anomalies "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def get_anomaly_stats(self) -> list[tuple[str, int]]:
        with sqlite3.connect(self.path) as conn:
            return conn.execute(
                "SELECT param, COUNT(*) AS cnt FROM anomalies "
                "GROUP BY param ORDER BY cnt DESC"
            ).fetchall()

    def get_total_readings(self) -> int:
        with sqlite3.connect(self.path) as conn:
            return conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]

    def get_total_anomalies(self) -> int:
        with sqlite3.connect(self.path) as conn:
            return conn.execute("SELECT COUNT(*) FROM anomalies").fetchone()[0]

    def get_last_anomalies_by_param(self) -> dict[str, str]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT param, MAX(ts) FROM anomalies GROUP BY param"
            ).fetchall()
        return dict(rows)

    def export_csv(self, filepath: str, limit: int = 5000) -> int:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT ts, param, value FROM readings ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Czas", "Parametr", "Warto\u015b\u0107"])
            writer.writerows(rows)
        return len(rows)

    def export_anomalies_csv(self, filepath: str) -> int:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT ts, param, value, reason FROM anomalies ORDER BY id DESC"
            ).fetchall()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Czas", "Parametr", "Warto\u015b\u0107", "Pow\u00f3d"])
            writer.writerows(rows)
        return len(rows)

    def clear_all(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.executescript("DELETE FROM readings; DELETE FROM anomalies;")


def _fmt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")