import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import make_db  # noqa: E402


@pytest.fixture
def scan_db():
    """Centralized in-memory SQLite database for scan integration tests.

    Delegates to db_test_helpers.make_db() - the canonical schema/views
    shared by the rest of the suite - rather than a local copy. The local
    copy this replaced had drifted from production: Events used pre-rename
    column names (eve_MAC instead of eveMac, see migrate_to_camelcase()),
    and Devices carried devNameLocked/devTypeLocked/devIconLocked/
    devTypeSource columns that don't exist in server/db/schema/app.sql and
    that no production code reads or writes - field locking is actually
    expressed via the LOCKED/USER/NEWDEV/<plugin> sentinel values already
    stored in the real *Source columns, not separate boolean columns.
    """
    conn = make_db()
    yield conn
    conn.close()
