from datetime import datetime, timedelta
from logger import mylog
from database import get_temp_db_connection


# -------------------------------------------------------------------------------
# Event handling (Matches table: Events)
# -------------------------------------------------------------------------------
class EventInstance:

    def _conn(self):
        """Always return a new DB connection (thread-safe)."""
        return get_temp_db_connection()

    def _rows_to_list(self, rows):
        return [dict(r) for r in rows]

    # Get all events
    def get_all(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM Events ORDER BY eve_DateTime DESC"
        ).fetchall()
        conn.close()
        return self._rows_to_list(rows)

    # --- Get last n events ---
    def get_last_n(self, n=10):
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM Events
            ORDER BY eve_DateTime DESC
            LIMIT ?
        """, (n,)).fetchall()
        conn.close()
        return self._rows_to_list(rows)

    # --- Specific helper for last 10 ---
    def get_last(self):
        return self.get_last_n(10)

    # Get events in the last 24h
    def get_recent(self):
        since = datetime.now() - timedelta(hours=24)
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM Events
            WHERE eve_DateTime >= ?
            ORDER BY eve_DateTime DESC
        """, (since,)).fetchall()
        conn.close()
        return self._rows_to_list(rows)

    # Get events from last N hours
    def get_by_hours(self, hours: int):
        if hours <= 0:
            mylog("warn", f"[Events] get_by_hours({hours}) -> invalid value")
            return []

        since = datetime.now() - timedelta(hours=hours)
        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM Events
            WHERE eve_DateTime >= ?
            ORDER BY eve_DateTime DESC
        """, (since,)).fetchall()
        conn.close()
        return self._rows_to_list(rows)

    # Get events in a date range
    def get_by_range(self, start: datetime, end: datetime):
        if end < start:
            mylog("error", f"[Events] get_by_range invalid: {start} > {end}")
            raise ValueError("Start must not be after end")

        conn = self._conn()
        rows = conn.execute("""
            SELECT * FROM Events
            WHERE eve_DateTime BETWEEN ? AND ?
            ORDER BY eve_DateTime DESC
        """, (start, end)).fetchall()
        conn.close()
        return self._rows_to_list(rows)

    # Insert new event
    def add(self, mac, ip, eventType, info="", pendingAlert=True, pairRow=None):
        conn = self._conn()
        conn.execute("""
            INSERT INTO Events (
                eve_MAC, eve_IP, eve_DateTime,
                eve_EventType, eve_AdditionalInfo,
                eve_PendingAlertEmail, eve_PairEventRowid
            ) VALUES (?,?,?,?,?,?,?)
        """, (mac, ip, datetime.now(), eventType, info,
              1 if pendingAlert else 0, pairRow))
        conn.commit()
        conn.close()

    # Delete old events
    def delete_older_than(self, days: int):
        cutoff = datetime.now() - timedelta(days=days)
        conn = self._conn()
        result = conn.execute("DELETE FROM Events WHERE eve_DateTime < ?", (cutoff,))
        conn.commit()
        deleted_count = result.rowcount
        conn.close()
        return deleted_count
