"""Shared database operations for device tracking"""

import os
import sqlite3
from datetime import datetime


class DeviceDatabase:
    """SQLite database for tracking programmed and tested devices"""

    def __init__(self, db_path="data/devices.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._create_tables()

    def _create_tables(self):
        """Create initial database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_name TEXT PRIMARY KEY,
                    programmed_at TEXT NOT NULL,
                    backpack_model TEXT,
                    test_status TEXT,
                    test_completed_at TEXT,
                    report_path TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_programmed_at "
                         "ON devices(programmed_at DESC)")
            conn.commit()

    def insert_device(
        self, device_name: str, backpack_model: str | None = None
    ):
        """Insert a newly programmed device"""

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO devices
                (device_name, programmed_at, backpack_model, test_status)
                VALUES (?, ?, ?, 'pending')
            """,
                (device_name, timestamp, backpack_model),
            )
            conn.commit()

    def update_test_status(
        self, device_name: str, status: str, report_path: str | None = None
    ):
        """Update test status for an existing device"""

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE devices
                SET test_status = ?, test_completed_at = ?, report_path = ?
                WHERE device_name = ?
            """,
                (status, timestamp, report_path, device_name),
            )
            conn.commit()

    def device_exists(self, device_name: str) -> bool:
        """Check if a device exists in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM devices WHERE device_name = ?", (device_name,)
            )
            return cursor.fetchone() is not None
