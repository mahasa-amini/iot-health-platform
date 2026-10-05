from sqlalchemy import text

from storage.base import Base


def initialize_schema(engine) -> None:
    """Create the schema and apply idempotent SQLite schema upgrades."""
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_active_assignment_wristband
            ON WRISTBAND_ASSIGNMENT (wristband_id)
            WHERE end_date IS NULL
        """))
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_active_assignment_patient
            ON WRISTBAND_ASSIGNMENT (patient_id)
            WHERE end_date IS NULL
        """))
