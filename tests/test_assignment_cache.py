import importlib
import sys
from pathlib import Path
from unittest.mock import Mock, patch


DASHBOARD_BACKEND = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "dashboard-backend"
)
sys.path.insert(0, str(DASHBOARD_BACKEND))

assignment_cache = importlib.import_module(
    "app.services.assignment_cache"
)


def test_assignment_lookup_does_not_return_stale_patient():
    first_response = Mock()
    first_response.status_code = 200
    first_response.json.return_value = {"patient_id": 10}

    second_response = Mock()
    second_response.status_code = 200
    second_response.json.return_value = {"patient_id": 20}

    with patch.object(
        assignment_cache.requests,
        "get",
        side_effect=[first_response, second_response],
    ) as mock_get:
        first_patient = assignment_cache.get_patient_id_for_wristband(1)
        second_patient = assignment_cache.get_patient_id_for_wristband(1)

    assert first_patient == 10
    assert second_patient == 20
    assert mock_get.call_count == 2
