from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from storage.local import engine

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/by-wristband/{wristband_id}")
def get_assignment_by_wristband(wristband_id: int):
    """
    Resolve active assignment and patient profile for a wristband.
    Used by Risk Analysis Service.
    """
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    wa.assignment_id,
                    p.patient_id,
                    p.threshold_profile
                FROM WRISTBAND_ASSIGNMENT wa
                JOIN PATIENT p ON p.patient_id = wa.patient_id
                WHERE wa.wristband_id = :wid
                  AND wa.end_date IS NULL
                """
            ),
            {"wid": wristband_id},
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No active assignment for wristband {wristband_id}"
        )

    return {
        "assignment_id": row.assignment_id,
        "patient_id": row.patient_id,
        "threshold_profile": row.threshold_profile,
    }

@router.get("/active")
def get_active_assignments():
    """
    Return all wristbands that currently have an active assignment.
    Used by Wristband Simulator.
    """
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT
                    wa.wristband_id
                FROM WRISTBAND_ASSIGNMENT wa
                WHERE wa.end_date IS NULL
                """
            )
        ).fetchall()

    return [
        {"wristband_id": row.wristband_id}
        for row in rows
    ]
