# Health Catalog Service

Health Catalog is the **central configuration hub** of the IoT Health Platform.
All other services must load their runtime configuration from this service (Phase 2 policy: **no hardcoding**).



## What Health Catalog Provides

Health Catalog stores and serves **mostly static** configuration:

- MQTT topic templates and patterns (vitals/alerts)
- Default threshold profiles for vitals (HR, SpO₂, Temperature)
- Service REST endpoints (base URLs)
- Alert contract (allowed statuses, severities, types, schema)
- Feature flags to enable/disable capabilities without code changes

> Important:
> - **Health Catalog = rules & configuration**
> - **DB = operational data & real system state**
> - Wristband → Patient mapping is **dynamic** and must come from DB (`WRISTBAND_ASSIGNMENT`).

--------

## Project Structure

health-catalog/
├─ README.md
└─ config/
    ├─ environments.json
    ├─ services.json
    ├─ mqtt_topics.json
    ├─ thresholds.json
    ├─ alerts.json
    └─ feature_flags.json


---

## Configuration Files

### environments.json
Defines runtime environments such as `local`, `docker`, and `cloud`.
Specifies:
- active environment
- MQTT broker host and port
- base networking defaults per environment

Used to switch environments without changing code.

---

### services.json
Defines REST service locations.

Each service entry includes:
- service name
- base_url
- optional version

Used by services to discover where other REST APIs are located.

---

### mqtt_topics.json
Defines MQTT topic contracts and patterns.

Includes:
- vitals topic template: `wristbands/{wristbandId}/vitals`
- vitals subscribe pattern: `wristbands/+/vitals`
- alerts publish pattern (Phase 2): `health/alerts`
- alerts subscribe patterns: `health/alerts` or `health/alerts/#`

All services must load MQTT topics from this file.

---

### thresholds.json
Defines default threshold profiles for vital signs.

Profiles are aligned with database constraints:
- STANDARD
- CARDIAC
- ELDERLY
- RESPIRATORY_RISK
- HIGH_RISK

Each profile defines normal, warning, and critical ranges for:
- heart rate (hr)
- SpO₂ (spo2)
- temperature

---

### alerts.json
Defines the alert contract shared by all services.

Includes:
- allowed alert types
- allowed severities
- allowed statuses
- lifecycle transitions
- payload schema and example

Alert statuses are aligned with database CHECK constraints:
- JUST_GENERATED
- ACKNOWLEDGED
- CLINICALLY_ASSESSED
- CLOSED

Health Catalog defines the contract; lifecycle execution is handled by backend services.

---

### feature_flags.json
Controls enabling and disabling features without code changes.

Phase 2 policy enforced via flags:
- all services must use Health Catalog
- no hardcoded configuration allowed
- vitals and alerts persistence enabled via MQTT
- wristband → patient mapping source is DB
- strict schema validation enabled

Used to support gradual rollout and controlled migration.

---

## Phase 2 Policy (Mandatory)

- All services must load configuration from Health Catalog
- No hardcoded topics, thresholds, endpoints, or alert rules
- MQTT is the source for vitals and alerts persistence
- Database remains the source of dynamic system state

---

## Status

This module currently provides the **configuration and design layer**.
REST API implementation and automated tests will be added in the next phase.


