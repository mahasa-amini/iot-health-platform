import sys
from pathlib import Path

import pytest

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


def test_dashboard_patients_in_risk_counts_lowercase_critical_alert(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard-risk.db"

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

        conn.execute(text("""
            INSERT INTO PATIENT (patient_id, name)
            VALUES (1, 'Patient 1')
        """))

        conn.execute(text("""
            INSERT INTO WRISTBAND (wristband_id)
            VALUES (1)
        """))

        conn.execute(text("""
            INSERT INTO WRISTBAND_ASSIGNMENT
                (assignment_id, wristband_id, patient_id, start_date, end_date)
            VALUES
                (1, 1, 1, CURRENT_TIMESTAMP, NULL)
        """))

        conn.execute(text("""
            INSERT INTO ALERT (
                alert_id,
                assignment_id,
                severity,
                alert_type,
                description,
                generated_at,
                status
            )
            VALUES (
                1,
                1,
                'critical',
                'THRESHOLD_BREACH',
                'Critical test alert',
                CURRENT_TIMESTAMP,
                'JUST_GENERATED'
            )
        """))

    result = local.LocalStorage().get_dashboard_overview()

    assert result["stats"]["patients_in_risk"] == 1


def test_count_critical_alerts_counts_lowercase_critical(tmp_path, monkeypatch):
    db_path = tmp_path / "critical-alerts.db"

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
            CREATE TABLE ALERT (
                alert_id INTEGER PRIMARY KEY,
                severity TEXT,
                status TEXT
            )
        """))

        conn.execute(text("""
            INSERT INTO ALERT (alert_id, severity, status)
            VALUES
                (1, 'critical', 'JUST_GENERATED'),
                (2, 'warning', 'JUST_GENERATED')
        """))

    result = local.LocalStorage().count_critical_alerts()

    assert result == 1


@pytest.mark.parametrize("severity", ["warning", "critical"])
def test_dashboard_response_accepts_lowercase_alert_severity(severity):
    dashboard_backend = ROOT / "services" / "dashboard-backend"
    sys.path.insert(0, str(dashboard_backend))

    from app.models.schemas import DashboardOverviewResponse

    payload = {
        "system_overview": {
            "active_devices": 1,
            "patients_monitored": 1,
            "active_alerts": 1,
            "last_update": "2026-01-01T00:00:00Z",
        },
        "stats": {
            "patients_in_risk": 1,
            "low_battery_devices": 0,
        },
        "recent_alerts": [
            {
                "alert_id": 1,
                "severity": severity,
                "alert_type": "THRESHOLD_BREACH",
                "description": "Critical test alert",
                "device_id": "WB-1",
                "generated_at": "2026-01-01T00:00:00Z",
                "acknowledged": False,
                "patient_name": "Patient 1",
            }
        ],
    }

    result = DashboardOverviewResponse.model_validate(payload)

    assert result.recent_alerts[0].severity.value == severity
