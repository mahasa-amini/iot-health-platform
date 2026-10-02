# iot-health-platform
IoT Platform for Smart Health Monitoring (Course Project)
#  IoT Health Monitoring Platform

A modular, scalable **IoT-based health monitoring system** for real-time patient vitals tracking, alert management, and clinical dashboards.

---

##  Overview

This project implements a **distributed microservice architecture** designed to monitor patients using wearable wristbands.  
It supports real-time vital collection, alert lifecycle management, and UI-ready dashboards.

The system is composed of **6 main layers**:

- **UI (Frontend)** – Clinician dashboard
- **Dashboard Backend API** – UI-oriented orchestration
- **Data Storage Service** – Database & domain logic
- **MQTT BROKER** - Broker as a Hub for Payloads
- **Risk Analysis** - Creating Risk Events Based On Profiles and Vital Payloads
- **Alert Notification** - Managing Alerts
- **Health Catalog** - Source Of Truth In Configuration Area

---

##  High-Level Architecture

```mermaid
flowchart LR
    UI[UI / Frontend]
    DBE[Dashboard Backend API]
    DS[Data Storage Service]
    RA[Risk Analysis Service]
    AL[Alert Notification Service]
    BR[Broker]
    WRS[Wristband Simulator]
    DB[Data Base]
    H[Health Catalog]

    UI -->|REST & WS| DBE
    DBE -->|REST| DS
    DS -->|REST| DBE
    DS --> DB
    H -->|REST| DS
    H -->|REST| DBE
    H -->|REST| RA
    H -->|REST| AL
    RA -->|MQTT| AL
    AL -->|MQTT| DS
    AL -->|MQTT| DBE
    WRS -->|MQTT| BR
    BR -->|MQTT| DBE
    BR -->|MQTT| DS
    BR -->|MQTT| RA
```
##  Design Principle

Dashboard Backend never accesses the database directly.  
All persistence and domain logic live exclusively in Data Storage.

---

##  Services Description

###  UI (Frontend)

Consumes REST APIs from Dashboard Backend.

Displays:

- Patients & details  
- Live vitals  
- Alerts & acknowledgments  
- Wristband management  

---

###  Dashboard Backend (FastAPI)

**Role:** UI-oriented orchestration layer

**Responsibilities:**

- Aggregate data into UI-ready structures  
- Transform domain data → presentation models  
- Handle endpoints:
  - `/dashboard/overview`
  - `/patients`
  - `/vitals`
  - `/alerts`
  - `/wristbands`

**Does NOT:**

- Store data  
- Run SQL  
- Generate timestamps for persistence  

---

### Data Storage Service (FastAPI + SQLAlchemy)

**Role:** Single source of truth

**Responsibilities:**

- Database access & transactions  
- Domain consistency  
- Alert lifecycle management  
- Assignment integrity  

**Generates internally:**

- `created_at`  
- `generated_at`  
- `acknowledged_at`  
- `start_date` / `end_date`  

---

## Database Schema (ERD)

```mermaid
erDiagram
    PATIENT ||--o{ WRISTBAND_ASSIGNMENT : has
    WRISTBAND ||--o{ WRISTBAND_ASSIGNMENT : assigned_to
    WRISTBAND_ASSIGNMENT ||--o{ VITAL_MEASUREMENT : produces
    WRISTBAND_ASSIGNMENT ||--o{ ALERT : triggers

    PATIENT {
        int patient_id PK
        string name
        int age
        string gender
        string phone
        string threshold_profile
    }

    WRISTBAND {
        int wristband_id PK
        datetime created_at
    }

    WRISTBAND_ASSIGNMENT {
        int assignment_id PK
        int patient_id FK
        int wristband_id FK
        datetime start_date
        datetime end_date
    }

    VITAL_MEASUREMENT {
        int measurement_id PK
        int assignment_id FK
        datetime measured_at
        int heart_rate
        int spo2
        float temperature
        float motion
        int battery_level
    }

    ALERT {
        int alert_id PK
        int assignment_id FK
        datetime generated_at
        datetime acknowledged_at
        string severity
        string status
        string reviewed_by
        string clinical_note
        string metric
        float value
        string description
        string full_description
    }
```


##  Key Design Decisions

- Strict service boundaries  
- No shared database access  
- UI schemas isolated from DB schemas  
- All timestamps generated server-side  
- Assignments guarantee medical correctness  
- REST-first architecture  

---

##  Tech Stack

- **FastAPI** – REST APIs  
- **SQLAlchemy** – ORM  
- **PostgreSQL / SQLite**  
- **MQTT** – IoT ingestion  
- **Docker & Docker Compose**  
- **Pydantic** – Validation  
- **Uvicorn** – ASGI server  

---

##  Features

- Patient management  
- Wristband assignment & unassignment  
- Real-time vitals ingestion  
- Alerts lifecycle & acknowledgment  
- Dashboard overview & stats  
- Low battery detection  
- Clean microservice architecture  
