from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


def load_config(filename: str) -> dict:
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{filename} not found")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
