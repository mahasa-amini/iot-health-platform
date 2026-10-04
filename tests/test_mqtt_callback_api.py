import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MQTT_CLIENT_FILES = [
    ROOT / "services" / "data-storage" / "src" / "mqtt_client.py",
    ROOT / "services" / "risk_analysis" / "main.py",
    ROOT / "services" / "alert_notification" / "main.py",
    ROOT / "services" / "dashboard-backend" / "app" / "mqtt" / "vital_subscriber.py",
    ROOT / "services" / "dashboard-backend" / "app" / "mqtt" / "alert_subscriber.py",
]


def test_all_persistent_mqtt_clients_use_callback_api_v2():
    failures = []

    for path in MQTT_CLIENT_FILES:
        tree = ast.parse(path.read_text())

        client_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "mqtt"
            and node.func.attr == "Client"
        ]

        assert client_calls, f"No mqtt.Client() found in {path}"

        for call in client_calls:
            version2 = False

            for keyword in call.keywords:
                if keyword.arg != "callback_api_version":
                    continue

                value = keyword.value
                version2 = (
                    isinstance(value, ast.Attribute)
                    and value.attr == "VERSION2"
                )

            if not version2:
                failures.append(str(path.relative_to(ROOT)))

    assert not failures, (
        "MQTT clients still using deprecated callback API v1: "
        + ", ".join(failures)
    )
