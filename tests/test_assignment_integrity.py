import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
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
