import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_ENV_URLS = {
    ROOT / "services/risk_analysis/main.py": {
        "HEALTH_CATALOG_URL": "http://health-catalog:8000",
        "DATA_STORAGE_URL": "http://data-storage:8003",
    },
    ROOT / "services/alert_notification/main.py": {
        "HEALTH_CATALOG_URL": "http://health-catalog:8000",
    },
    ROOT / "services/dashboard-backend/app/services/assignment_cache.py": {
        "DATA_STORAGE_URL": "http://data-storage:8003",
    },
    ROOT / "services/dashboard-backend/app/services/rest_storage_client.py": {
        "DATA_STORAGE_URL": "http://data-storage:8003",
    },
}


def _env_defaults(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text())
    found = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue

        target = node.targets[0]
        value = node.value

        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "os"
            and value.func.attr == "getenv"
            and len(value.args) >= 2
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[1], ast.Constant)
        ):
            found[value.args[0].value] = value.args[1].value

    return found


def test_service_urls_are_environment_configurable():
    failures = []

    for path, expected in EXPECTED_ENV_URLS.items():
        actual = _env_defaults(path)

        for env_name, default in expected.items():
            if actual.get(env_name) != default:
                failures.append(
                    f"{path.relative_to(ROOT)} must use "
                    f'os.getenv("{env_name}", "{default}")'
                )

    assert not failures, "\n".join(failures)


def test_rest_storage_client_adds_api_prefix_itself():
    path = ROOT / "services/dashboard-backend/app/services/rest_storage_client.py"
    source = path.read_text()

    assert '"http://data-storage:8003/api/v1"' not in source
    assert "/api/v1" in source
