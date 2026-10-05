import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

from storage import local  # noqa: E402


def test_dashboard_active_devices_counts_active_wristbands(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.db"

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(local, "SessionLocal", TestSessionLocal)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE PATIENT (
                patient_id INTEGER PRIMARY KEY,
                name TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE WRISTBAND (
                wristband_id INTEGER PRIMARY KEY
            )
        """))

        conn.execute(text("""
            CREATE TABLE WRISTBAND_ASSIGNMENT (
                assignment_id INTEGER PRIMARY KEY,
                wristband_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                start_date DATETIME,
                end_date DATETIME
            )
        """))

        conn.execute(text("""
            CREATE TABLE ALERT (
                alert_id INTEGER PRIMARY KEY,
                assignment_id INTEGER NOT NULL,
                severity TEXT,
                alert_type TEXT,
                description TEXT,
                generated_at DATETIME,
                status TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE VITAL_MEASUREMENT (
                measurement_id INTEGER PRIMARY KEY,
                assignment_id INTEGER NOT NULL,
                measured_at DATETIME,
                battery_level INTEGER
            )
        """))

        conn.execute(
            text("INSERT INTO PATIENT (patient_id, name) VALUES (1, 'Patient 1')")
        )

        conn.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id)
                VALUES (1), (2)
            """)
        )

        conn.execute(
            text("""
                INSERT INTO WRISTBAND_ASSIGNMENT
                    (assignment_id, wristband_id, patient_id, start_date, end_date)
                VALUES
                    (1, 1, 1, CURRENT_TIMESTAMP, NULL),
                    (2, 2, 1, CURRENT_TIMESTAMP, NULL)
            """)
        )

    result = local.LocalStorage().get_dashboard_overview()

    assert result["system_overview"]["active_devices"] == 2
