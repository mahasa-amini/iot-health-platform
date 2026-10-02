from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    CheckConstraint,
)
from storage.base import Base
from datetime import datetime


# ----------------------------
# Core domain entities
# ----------------------------
class Wristband(Base):
    __tablename__ = "WRISTBAND"

    wristband_id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )


class Patient(Base):
    __tablename__ = "PATIENT"

    patient_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(
        String(10),
        CheckConstraint("gender IN ('MALE','FEMALE')"),
        nullable=False,
    )
    phone = Column(String(15))
    
    threshold_profile = Column(
        String(30),
        CheckConstraint(
            "threshold_profile IN "
            "('STANDARD','CARDIAC','ELDERLY','RESPIRATORY_RISK','HIGH_RISK')"
        ),
        nullable=False,
    )


class WristbandAssignment(Base):
    __tablename__ = "WRISTBAND_ASSIGNMENT"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    wristband_id = Column(
        Integer, ForeignKey("WRISTBAND.wristband_id"), nullable=False
    )
    patient_id = Column(
        Integer, ForeignKey("PATIENT.patient_id"), nullable=False
    )
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime)


# ----------------------------
# Measurements
# ----------------------------
class VitalMeasurement(Base):
    __tablename__ = "VITAL_MEASUREMENT"

    measurement_id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(
        Integer,
        ForeignKey("WRISTBAND_ASSIGNMENT.assignment_id"),
        nullable=False,
    )
    measured_at = Column(DateTime, nullable=False)

    heart_rate = Column(Integer)
    spo2 = Column(Integer)
    temperature = Column(Float)
    motion = Column(Float)
    battery_level = Column(
        Integer,
        CheckConstraint("battery_level BETWEEN 0 AND 100"),
    )


# ----------------------------
# Alerts (final, UI-ready)
# ----------------------------
class Alert(Base):
    __tablename__ = "ALERT"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)

    assignment_id = Column(
        Integer,
        ForeignKey("WRISTBAND_ASSIGNMENT.assignment_id"),
        nullable=False,
    )

    # Timestamps
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    reviewed_at = Column(DateTime)

    # Clinical workflow
    reviewed_by = Column(String(50))
    clinical_note = Column(String)

    # Alert classification
    alert_type = Column(String(30), nullable=False)
    severity = Column(
        String(20),
        CheckConstraint("severity IN ('normal','warning','critical')"),
        nullable=False,
    )

    status = Column(
        String(30),
        CheckConstraint(
            "status IN ("
            "'JUST_GENERATED',"
            "'ACKNOWLEDGED',"
            "'CLINICALLY_ASSESSED',"
            "'CLOSED'"
            ")"
        ),
        nullable=False,
        default="JUST_GENERATED",
    )

    threshold_profile = Column(String(30), nullable=False)

    # UI-focused fields
    metric = Column(String(30), nullable=False)
    value = Column(Float, nullable=False)

    description = Column(String, nullable=False)
    full_description = Column(String, nullable=False)
