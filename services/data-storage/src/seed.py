from datetime import datetime, timezone

from models import Patient, Wristband, WristbandAssignment
from storage.local import SessionLocal


DEMO_DATA = [
    {
        "patient_id": 1,
        "name": "Demo Patient Standard",
        "age": 35,
        "gender": "MALE",
        "phone": None,
        "threshold_profile": "STANDARD",
        "wristband_id": 1,
    },
    {
        "patient_id": 2,
        "name": "Demo Patient Cardiac",
        "age": 65,
        "gender": "FEMALE",
        "phone": None,
        "threshold_profile": "CARDIAC",
        "wristband_id": 2,
    },
    {
        "patient_id": 3,
        "name": "Demo Patient Respiratory",
        "age": 55,
        "gender": "MALE",
        "phone": None,
        "threshold_profile": "RESPIRATORY_RISK",
        "wristband_id": 3,
    },
]


def seed_demo_data(session=None) -> None:
    owns_session = session is None
    if owns_session:
        session = SessionLocal()

    try:
        # Seed demo records only for a fresh database.
        if session.query(Patient).first() is not None:
            print("[SEED] Existing data found; skipping demo seed")
            return

        for item in DEMO_DATA:
            patient = session.get(Patient, item["patient_id"])
            if patient is None:
                patient = Patient(
                    patient_id=item["patient_id"],
                    name=item["name"],
                    age=item["age"],
                    gender=item["gender"],
                    phone=item["phone"],
                    threshold_profile=item["threshold_profile"],
                )
                session.add(patient)

            wristband = session.get(Wristband, item["wristband_id"])
            if wristband is None:
                wristband = Wristband(
                    wristband_id=item["wristband_id"],
                    created_at=datetime.now(timezone.utc),
                )
                session.add(wristband)

            session.flush()

            assignment = (
                session.query(WristbandAssignment)
                .filter(
                    WristbandAssignment.patient_id == item["patient_id"],
                    WristbandAssignment.wristband_id == item["wristband_id"],
                    WristbandAssignment.end_date.is_(None),
                )
                .first()
            )

            if assignment is None:
                session.add(
                    WristbandAssignment(
                        wristband_id=item["wristband_id"],
                        patient_id=item["patient_id"],
                        start_date=datetime.now(timezone.utc),
                    )
                )

        session.commit()
        print("[SEED] Demo data ready")

    except Exception:
        session.rollback()
        raise

    finally:
        if owns_session:
            session.close()
