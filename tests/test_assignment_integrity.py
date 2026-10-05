import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


DATA_STORAGE_SRC = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "data-storage"
    / "src"
)
sys.path.insert(0, str(DATA_STORAGE_SRC))

from storage import local
from storage.local import LocalStorage
from storage.base import Base


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    db_path = tmp_path / "assignment-integrity.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(local, "SessionLocal", TestingSessionLocal)

    yield LocalStorage(), TestingSessionLocal

    engine.dispose()


def test_cannot_assign_active_wristband_to_second_patient(isolated_storage):
    storage, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES (1, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Patient One', 40, 'FEMALE', NULL, 'STANDARD'),
                    (2, 'Patient Two', 50, 'MALE', NULL, 'STANDARD')
            """)
        )
        session.commit()
    finally:
        session.close()

    storage.assign_wristband(patient_id=1, wristband_id=1)

    with pytest.raises(ValueError, match="already assigned"):
        storage.assign_wristband(patient_id=2, wristband_id=1)


def test_cannot_assign_second_active_wristband_to_same_patient(isolated_storage):
    storage, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES
                    (1, CURRENT_TIMESTAMP),
                    (2, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Patient One', 40, 'FEMALE', NULL, 'STANDARD')
            """)
        )
        session.commit()
    finally:
        session.close()

    storage.assign_wristband(patient_id=1, wristband_id=1)

    with pytest.raises(ValueError, match="already has an active wristband"):
        storage.assign_wristband(patient_id=1, wristband_id=2)


def test_reassignment_allowed_after_previous_assignment_ends(isolated_storage):
    storage, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES
                    (1, CURRENT_TIMESTAMP),
                    (2, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Patient One', 40, 'FEMALE', NULL, 'STANDARD'),
                    (2, 'Patient Two', 50, 'MALE', NULL, 'STANDARD')
            """)
        )
        session.commit()
    finally:
        session.close()

    storage.assign_wristband(patient_id=1, wristband_id=1)
    assert storage.unassign_wristband(wristband_id=1) is True

    # Same patient may receive a new wristband after the old assignment ended.
    storage.assign_wristband(patient_id=1, wristband_id=2)
    assert storage.unassign_wristband(wristband_id=2) is True

    # The original wristband may later be assigned to another patient.
    storage.assign_wristband(patient_id=2, wristband_id=1)

    session = SessionLocal()
    try:
        active = session.execute(
            text("""
                SELECT patient_id, wristband_id
                FROM WRISTBAND_ASSIGNMENT
                WHERE end_date IS NULL
            """)
        ).all()
    finally:
        session.close()

    assert active == [(2, 1)]


def test_create_patient_rolls_back_when_wristband_assignment_fails(isolated_storage):
    storage, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES (1, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Existing Patient', 40, 'FEMALE', NULL, 'STANDARD')
            """)
        )
        session.commit()
    finally:
        session.close()

    storage.assign_wristband(patient_id=1, wristband_id=1)

    with pytest.raises(ValueError, match="already assigned"):
        storage.create_patient(
            {
                "name": "Should Not Persist",
                "age": 50,
                "gender": "MALE",
                "phone": None,
                "threshold_profile": "STANDARD",
                "wristband_id": 1,
            }
        )

    session = SessionLocal()
    try:
        patient_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM PATIENT
                WHERE name = 'Should Not Persist'
            """)
        ).scalar_one()
    finally:
        session.close()

    assert patient_count == 0


def test_create_patient_commits_patient_and_wristband_together(isolated_storage):
    storage, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES (1, CURRENT_TIMESTAMP)
            """)
        )
        session.commit()
    finally:
        session.close()

    result = storage.create_patient(
        {
            "name": "New Patient",
            "age": 35,
            "gender": "FEMALE",
            "phone": None,
            "threshold_profile": "STANDARD",
            "wristband_id": 1,
        }
    )

    session = SessionLocal()
    try:
        row = session.execute(
            text("""
                SELECT p.name, wa.wristband_id
                FROM PATIENT p
                JOIN WRISTBAND_ASSIGNMENT wa
                    ON wa.patient_id = p.patient_id
                WHERE p.patient_id = :patient_id
                  AND wa.end_date IS NULL
            """),
            {"patient_id": result["patient_id"]},
        ).first()
    finally:
        session.close()

    assert row == ("New Patient", 1)


def test_database_rejects_two_active_assignments_for_same_wristband(
    isolated_storage,
):
    _, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES (1, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Patient One', 40, 'FEMALE', NULL, 'STANDARD'),
                    (2, 'Patient Two', 50, 'MALE', NULL, 'STANDARD')
            """)
        )
        session.execute(
            text("""
                INSERT INTO WRISTBAND_ASSIGNMENT
                    (wristband_id, patient_id, start_date, end_date)
                VALUES
                    (1, 1, CURRENT_TIMESTAMP, NULL)
            """)
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                text("""
                    INSERT INTO WRISTBAND_ASSIGNMENT
                        (wristband_id, patient_id, start_date, end_date)
                    VALUES
                        (1, 2, CURRENT_TIMESTAMP, NULL)
                """)
            )
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_database_rejects_two_active_wristbands_for_same_patient(
    isolated_storage,
):
    _, SessionLocal = isolated_storage

    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO WRISTBAND (wristband_id, created_at)
                VALUES
                    (1, CURRENT_TIMESTAMP),
                    (2, CURRENT_TIMESTAMP)
            """)
        )
        session.execute(
            text("""
                INSERT INTO PATIENT
                    (patient_id, name, age, gender, phone, threshold_profile)
                VALUES
                    (1, 'Patient One', 40, 'FEMALE', NULL, 'STANDARD')
            """)
        )
        session.execute(
            text("""
                INSERT INTO WRISTBAND_ASSIGNMENT
                    (wristband_id, patient_id, start_date, end_date)
                VALUES
                    (1, 1, CURRENT_TIMESTAMP, NULL)
            """)
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                text("""
                    INSERT INTO WRISTBAND_ASSIGNMENT
                        (wristband_id, patient_id, start_date, end_date)
                    VALUES
                        (2, 1, CURRENT_TIMESTAMP, NULL)
                """)
            )
            session.commit()
    finally:
        session.rollback()
        session.close()
