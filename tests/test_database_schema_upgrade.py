import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

import models  # noqa: E402,F401
from schema import initialize_schema  # noqa: E402


def test_existing_assignment_table_gets_active_assignment_indexes(tmp_path):
    db_path = tmp_path / "existing.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    # Simulate a database created before the active-assignment
    # partial unique indexes were introduced.
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE WRISTBAND_ASSIGNMENT (
                assignment_id INTEGER PRIMARY KEY,
                wristband_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME
            )
        """))

    initialize_schema(engine)

    with engine.connect() as conn:
        indexes = {
            row[0]
            for row in conn.execute(text("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND tbl_name = 'WRISTBAND_ASSIGNMENT'
            """))
        }

    assert "uq_active_assignment_wristband" in indexes
    assert "uq_active_assignment_patient" in indexes


def test_schema_initialization_is_idempotent(tmp_path):
    db_path = tmp_path / "idempotent.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    initialize_schema(engine)
    initialize_schema(engine)

    with engine.connect() as conn:
        indexes = {
            row[0]
            for row in conn.execute(text("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND tbl_name = 'WRISTBAND_ASSIGNMENT'
            """))
        }

    assert "uq_active_assignment_wristband" in indexes
    assert "uq_active_assignment_patient" in indexes


def test_schema_upgrade_rejects_existing_duplicate_active_assignments(tmp_path):
    db_path = tmp_path / "invalid-existing.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE WRISTBAND_ASSIGNMENT (
                assignment_id INTEGER PRIMARY KEY,
                wristband_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME
            )
        """))

        conn.execute(text("""
            INSERT INTO WRISTBAND_ASSIGNMENT
                (assignment_id, wristband_id, patient_id, start_date, end_date)
            VALUES
                (1, 10, 1, CURRENT_TIMESTAMP, NULL),
                (2, 10, 2, CURRENT_TIMESTAMP, NULL)
        """))

    with pytest.raises(IntegrityError):
        initialize_schema(engine)
