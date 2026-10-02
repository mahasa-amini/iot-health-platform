import os
from datetime import datetime, timezone

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from storage.base import StorageBackend
from models import VitalMeasurement, Alert


# ----------------------------
# Database setup
# ----------------------------
DB_PATH = os.getenv("DB_PATH", "/app/data/health.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ----------------------------
# Storage implementation
# ----------------------------
class LocalStorage(StorageBackend):
    """
    Local SQLite storage backend.
    Owns persistence logic and DB schema.
    """

    # ----------------------------
    # VITALS
    # ----------------------------
    def save_vital(self, assignment_id: int, data: dict) -> None:
        session = SessionLocal()
        try:
            measured_at = self._parse_datetime(data.get("measured_at"))

            row = VitalMeasurement(
                assignment_id=assignment_id,
                measured_at=measured_at,
                heart_rate=data.get("heart_rate"),
                spo2=data.get("spo2"),
                temperature=data.get("temperature"),
                motion=data.get("motion"),
                battery_level=data.get("battery_level"),
            )

            session.add(row)
            session.commit()
        finally:
            session.close()

    # ----------------------------
    # ALERTS
    # ----------------------------
    def save_alert(self, assignment_id: int, data: dict) -> None:
        session = SessionLocal()
        try:
            generated_at = self._parse_datetime(data.get("generated_at"))

            row = Alert(
                assignment_id=assignment_id,
                generated_at=generated_at,
                alert_type=data["alert_type"],
                severity=data["severity"],
                status=data.get("status", "JUST_GENERATED"),
                threshold_profile=data["threshold_profile"],
                metric=data["metric"],
                value=data["value"],
                description=data["description"],
                full_description=data["full_description"],
            )

            session.add(row)
            session.commit()
        finally:
            session.close()


    # ----------------------------
    # All Patients Overview
    # ----------------------------
    def get_patients_overview(self) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        p.patient_id,
                        p.name AS patient_name,
                        p.age,
                        p.gender,
                        p.phone,

                        wa.assignment_id,
                        w.wristband_id,

                        vm.measured_at AS last_update,
                        vm.heart_rate,
                        vm.spo2,
                        vm.temperature,
                        vm.battery_level,

                        la.severity AS latest_alert_severity

                    FROM PATIENT p
                    LEFT JOIN WRISTBAND_ASSIGNMENT wa
                        ON wa.patient_id = p.patient_id
                        AND wa.end_date IS NULL
                    LEFT JOIN WRISTBAND w
                        ON w.wristband_id = wa.wristband_id
                    LEFT JOIN VITAL_MEASUREMENT vm
                        ON vm.assignment_id = wa.assignment_id
                        AND vm.measured_at = (
                            SELECT MAX(vm2.measured_at)
                            FROM VITAL_MEASUREMENT vm2
                            WHERE vm2.assignment_id = wa.assignment_id
                        )
                    LEFT JOIN ALERT la
                        ON la.assignment_id = wa.assignment_id
                        AND la.status != 'ACKNOWLEDGED'
                        AND la.generated_at = (
                            SELECT MAX(a2.generated_at)
                            FROM ALERT a2
                            WHERE a2.assignment_id = wa.assignment_id
                              AND a2.status != 'ACKNOWLEDGED'
                        )
                    ORDER BY p.name
                """)
            ).mappings().all()

            return [dict(r) for r in rows]

        finally:
            session.close()

    # ----------------------------
    # Single Patient Overview
    # ----------------------------
    def get_patient_overview(self, patient_id: int) -> dict | None:
        session = SessionLocal()
        try:
            row = session.execute(
                text("""
                    SELECT
                        p.patient_id,
                        p.name AS patient_name,
                        p.age,
                        p.gender,
                        p.phone,

                        wa.assignment_id,
                        w.wristband_id,

                        vm.measured_at AS last_update,
                        vm.heart_rate,
                        vm.spo2,
                        vm.temperature,
                        vm.battery_level,

                        la.severity AS latest_alert_severity

                    FROM PATIENT p
                    LEFT JOIN WRISTBAND_ASSIGNMENT wa
                        ON wa.patient_id = p.patient_id
                        AND wa.end_date IS NULL
                    LEFT JOIN WRISTBAND w
                        ON w.wristband_id = wa.wristband_id
                    LEFT JOIN VITAL_MEASUREMENT vm
                        ON vm.assignment_id = wa.assignment_id
                        AND vm.measured_at = (
                            SELECT MAX(v2.measured_at)
                            FROM VITAL_MEASUREMENT v2
                            WHERE v2.assignment_id = wa.assignment_id
                        )
                    LEFT JOIN ALERT la
                        ON la.assignment_id = wa.assignment_id
                        AND la.status != 'ACKNOWLEDGED'
                        AND la.generated_at = (
                            SELECT MAX(a2.generated_at)
                            FROM ALERT a2
                            WHERE a2.assignment_id = wa.assignment_id
                              AND a2.status != 'ACKNOWLEDGED'
                        )
                    WHERE p.patient_id = :patient_id
                """),
                {"patient_id": patient_id},
            ).mappings().first()

            return dict(row) if row else None

        finally:
            session.close()

    # ----------------------------
    # Patient Alerts
    # ----------------------------
    def get_patient_alerts(self, patient_id: int) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        a.alert_id,
                        a.assignment_id,
                        a.generated_at,
                        a.severity,
                        a.status,
                        a.alert_type,
                        a.threshold_profile,
                        a.metric,
                        a.value,
                        a.description,
                        a.full_description,
                        wa.wristband_id
                    FROM ALERT a
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON a.assignment_id = wa.assignment_id
                    WHERE wa.patient_id = :patient_id
                    ORDER BY a.generated_at DESC
                """),
                {"patient_id": patient_id},
            ).mappings().all()

            return [dict(r) for r in rows]

        finally:
            session.close()

    # ----------------------------
    # Create Patient
    # ----------------------------
    def create_patient(self, data: dict) -> dict:
        session = SessionLocal()
        try:
            wristband_id = data.pop("wristband_id", None)

            res = session.execute(
                text("""
                    INSERT INTO PATIENT (name, age, gender, phone, threshold_profile)
                    VALUES (:name, :age, :gender, :phone, :threshold_profile)
                """),
                data,
            )

            patient_id = res.lastrowid
            session.commit()

            if wristband_id is not None:
                self.assign_wristband(patient_id, wristband_id)

            return {
                "patient_id": patient_id,
                "name": data["name"],
            }

        finally:
            session.close()

    # ----------------------------
    #  Wristband
    # ----------------------------
    def assign_wristband(self, patient_id: int, wristband_id: int) -> None:
        session = SessionLocal()
        try:
            session.execute(
                text("""
                    INSERT INTO WRISTBAND_ASSIGNMENT (
                        patient_id,
                        wristband_id,
                        start_date
                    )
                    VALUES (:patient_id, :wristband_id, CURRENT_TIMESTAMP)
                """),
                {
                    "patient_id": patient_id,
                    "wristband_id": wristband_id,
                },
            )
            session.commit()
        finally:
            session.close()

    def list_wristbands(self) -> list[dict]:
        """
        Return all wristbands with assigned patient (if any).
        """
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        w.wristband_id,
                        w.created_at,
                        p.name AS assigned_to
                    FROM WRISTBAND w
                    LEFT JOIN WRISTBAND_ASSIGNMENT wa
                        ON wa.wristband_id = w.wristband_id
                        AND wa.end_date IS NULL
                    LEFT JOIN PATIENT p
                        ON p.patient_id = wa.patient_id
                    ORDER BY w.wristband_id
                """)
            ).mappings().all()

            return [
                {
                    "wristband_id": r["wristband_id"],
                    "created_at": r["created_at"],
                    "assignedTo": r["assigned_to"],
                }
                for r in rows
            ]

        finally:
            session.close()

    def list_available_wristbands(self) -> list[dict]:
        """
        Return wristbands without an active assignment.
        """
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        w.wristband_id,
                        w.created_at
                    FROM WRISTBAND w
                    LEFT JOIN WRISTBAND_ASSIGNMENT wa
                        ON wa.wristband_id = w.wristband_id
                        AND wa.end_date IS NULL
                    WHERE wa.assignment_id IS NULL
                    ORDER BY w.wristband_id
                """)
            ).mappings().all()

            return [dict(r) for r in rows]

        finally:
            session.close()

    def create_wristband(self, wristband_id: int) -> dict:
        """
        Create a new wristband.
        - wristband_id comes from UI
        - created_at is generated by DB
        """
        session = SessionLocal()
        try:
            session.execute(
                text("""
                    INSERT INTO WRISTBAND (
                        wristband_id,
                        created_at
                    )
                    VALUES (
                        :wristband_id,
                        CURRENT_TIMESTAMP
                    )
                """),
                {"wristband_id": wristband_id,
                 "created_at": datetime.now(timezone.utc)}
            )

            session.commit()

                # row = session.execute(
                #     text("""
                #         SELECT
                #             wristband_id,
                #             created_at
                #         FROM WRISTBAND
                #         WHERE wristband_id = :wristband_id
                #     """),
                #     {"wristband_id": wristband_id}
                # ).mappings().first()

            return {"wristband_id": wristband_id,
                 "created_at": datetime.now(timezone.utc)}

        finally:
            session.close()


    def unassign_wristband(self, wristband_id: int) -> bool:
        session = SessionLocal()
        try:
            result = session.execute(
                text("""
                    UPDATE WRISTBAND_ASSIGNMENT
                    SET end_date = CURRENT_TIMESTAMP
                    WHERE wristband_id = :wristband_id
                    AND end_date IS NULL
                """),
                {"wristband_id": wristband_id}
            )

            session.commit()

            # rowcount = چند assignment بسته شده
            return result.rowcount > 0

        finally:
            session.close()
    # ----------------------------
    # list Alerts
    # ----------------------------
    def list_alerts(self) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        a.alert_id,
                        a.assignment_id,
                        a.generated_at,
                        a.severity,
                        a.status,
                        a.alert_type,
                        a.threshold_profile,
                        a.metric,
                        a.value,
                        a.description,
                        a.full_description,
                        wa.wristband_id,
                        p.name AS patient_name
                    FROM ALERT a
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON a.assignment_id = wa.assignment_id
                    JOIN PATIENT p
                        ON wa.patient_id = p.patient_id
                    ORDER BY a.generated_at DESC
                """)
            ).mappings().all()

            return [dict(r) for r in rows]
        finally:
            session.close()
    
    def acknowledge_alert(
        self,
        alert_id: int,
        reviewed_by: str | None = None,
        clinical_note: str | None = None,
        ) -> bool:
            session = SessionLocal()
            try:
                result = session.execute(
                    text("""
                        UPDATE ALERT
                        SET
                            status = 'ACKNOWLEDGED',
                            acknowledged_at = CURRENT_TIMESTAMP,
                            reviewed_by = :reviewed_by,
                            clinical_note = :clinical_note
                        WHERE alert_id = :alert_id
                    """),
                    {
                        "alert_id": alert_id,
                        "reviewed_by": reviewed_by,
                        "clinical_note": clinical_note,
                    },
                )

                session.commit()
                return result.rowcount > 0
            finally:
                session.close()

   # ----------------------------  
    # latest Vitals for all patients
    # ----------------------------
    def get_latest_vitals(self) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        vm.measured_at,
                        vm.heart_rate,
                        vm.spo2,
                        vm.temperature,
                        vm.motion,
                        vm.battery_level,

                        wa.assignment_id,
                        wa.wristband_id,
                        p.patient_id,
                        p.name AS patient_name

                    FROM VITAL_MEASUREMENT vm
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON vm.assignment_id = wa.assignment_id
                    JOIN PATIENT p
                        ON wa.patient_id = p.patient_id

                    WHERE wa.end_date IS NULL
                    AND vm.measured_at = (
                        SELECT MAX(vm2.measured_at)
                        FROM VITAL_MEASUREMENT vm2
                        WHERE vm2.assignment_id = vm.assignment_id
                    )

                    ORDER BY vm.measured_at DESC
                """)
            ).mappings().all()

            return [dict(r) for r in rows]
        finally:
            session.close()

    # ----------------------------  
    # latest Vitals for a patient with limit
    # ----------------------------
    def get_vitals_history(self, patient_id: int, limit: int = 50) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT
                        vm.measured_at,
                        vm.heart_rate,
                        vm.spo2,
                        vm.temperature,
                        vm.motion,
                        vm.battery_level

                    FROM VITAL_MEASUREMENT vm
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON vm.assignment_id = wa.assignment_id

                    WHERE wa.patient_id = :patient_id
                    AND wa.end_date IS NULL

                    ORDER BY vm.measured_at DESC
                    LIMIT :limit
                """),
                {
                    "patient_id": patient_id,
                    "limit": limit,
                }
            ).mappings().all()

            return [dict(r) for r in rows]
        finally:
            session.close()

    # ----------------------------  
    # dashboard counts
    # ----------------------------
    def count_patients(self) -> int:
        session = SessionLocal()
        try:
            result = session.execute(
                text("SELECT COUNT(*) FROM PATIENT")
            )
            return result.scalar_one()
        finally:
            session.close()

    def count_active_patients(self) -> int:
        session = SessionLocal()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(DISTINCT patient_id)
                    FROM WRISTBAND_ASSIGNMENT
                    WHERE end_date IS NULL
                """)
            )
            return result.scalar_one()
        finally:
            session.close()

    def count_active_alerts(self) -> int:
        session = SessionLocal()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM ALERT
                    WHERE status != 'ACKNOWLEDGED'
                """)
            )
            return result.scalar_one()
        finally:
            session.close()

    def count_critical_alerts(self) -> int:
        session = SessionLocal()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM ALERT
                    WHERE status != 'ACKNOWLEDGED'
                    AND severity = 'CRITICAL'
                """)
            )
            return result.scalar_one()
        finally:
            session.close()

    def count_low_battery_devices(self, threshold: int) -> int:
        session = SessionLocal()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM WRISTBAND_ASSIGNMENT wa
                    JOIN VITAL_MEASUREMENT vm
                    ON wa.assignment_id = vm.assignment_id
                    WHERE wa.end_date IS NULL
                    AND vm.measured_at = (
                        SELECT MAX(vm2.measured_at)
                        FROM VITAL_MEASUREMENT vm2
                        WHERE vm2.assignment_id = wa.assignment_id
                    )
                    AND vm.battery_level < :threshold
                """),
                {"threshold": threshold},
            )
            return result.scalar_one()
        finally:
            session.close()
    
    def get_dashboard_overview(self) -> dict:
        session = SessionLocal()
        try:
            now = datetime.now(timezone.utc)

            total_patients = session.execute(
                text("SELECT COUNT(*) FROM PATIENT")
            ).scalar_one()

            active_devices = session.execute(
                text("""
                    SELECT COUNT(DISTINCT patient_id)
                    FROM WRISTBAND_ASSIGNMENT
                    WHERE end_date IS NULL
                """)
            ).scalar_one()

            active_alerts = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM ALERT
                    WHERE status != 'ACKNOWLEDGED'
                """)
            ).scalar_one()

            patients_in_risk = session.execute(
                text("""
                    SELECT COUNT(DISTINCT wa.patient_id)
                    FROM ALERT a
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON a.assignment_id = wa.assignment_id
                    WHERE a.status != 'ACKNOWLEDGED'
                    AND a.severity = 'CRITICAL'
                """)
            ).scalar_one()

            low_battery_devices = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM WRISTBAND_ASSIGNMENT wa
                    JOIN VITAL_MEASUREMENT vm
                        ON wa.assignment_id = vm.assignment_id
                    WHERE wa.end_date IS NULL
                    AND vm.measured_at = (
                        SELECT MAX(vm2.measured_at)
                        FROM VITAL_MEASUREMENT vm2
                        WHERE vm2.assignment_id = wa.assignment_id
                    )
                    AND vm.battery_level < 30
                """)
            ).scalar_one()

            recent_alert_rows = session.execute(
                text("""
                    SELECT
                        a.alert_id,
                        a.severity,
                        a.alert_type,
                        a.description,
                        a.generated_at,
                        a.status,
                        w.wristband_id,
                        p.name AS patient_name
                    FROM ALERT a
                    JOIN WRISTBAND_ASSIGNMENT wa
                        ON a.assignment_id = wa.assignment_id
                    JOIN WRISTBAND w
                        ON wa.wristband_id = w.wristband_id
                    JOIN PATIENT p
                        ON wa.patient_id = p.patient_id
                    ORDER BY a.generated_at DESC
                    LIMIT 5
                """)
            ).mappings().all()

            recent_alerts = [
                {
                    "alert_id": r["alert_id"],
                    "severity": r["severity"],
                    "alert_type": r["alert_type"],
                    "description": r.get("description", ""),
                    "device_id": f"WB-{r['wristband_id']}",
                    "generated_at": r["generated_at"],
                    "acknowledged": r["status"] == "ACKNOWLEDGED",
                    "patient_name": r["patient_name"],
                }
                for r in recent_alert_rows
            ]

            return {
                "system_overview": {
                    "active_devices": active_devices,
                    "patients_monitored": total_patients,
                    "active_alerts": active_alerts,
                    "last_update": now,
                },
                "stats": {
                    "patients_in_risk": patients_in_risk,
                    "low_battery_devices": low_battery_devices,
                },
                "recent_alerts": recent_alerts,
            }

        finally:
            session.close()
    # ----------------------------
    # Query API (future phases)
    # ----------------------------
    def get_latest(self, assignment_id: int):
        return None

    def get_history(self, assignment_id: int, start=None, end=None):
        return []


    # ----------------------------
    # Helpers
    # ----------------------------
    @staticmethod
    def _parse_datetime(value):
        if not value:
            return datetime.utcnow()

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
