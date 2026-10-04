import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"

sys.path.insert(0, str(DATA_STORAGE_SRC))

import seed  # noqa: E402


def test_seed_skips_existing_database():
    session = MagicMock()

    # Any existing patient means this is not a fresh database.
    session.query.return_value.first.return_value = object()

    seed.seed_demo_data(session=session)

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_seed_populates_fresh_database():
    session = MagicMock()

    # Fresh database: no patient exists yet.
    session.query.return_value.first.return_value = None
    session.query.return_value.filter.return_value.first.return_value = None
    session.get.return_value = None

    seed.seed_demo_data(session=session)

    # 3 patients + 3 wristbands + 3 assignments.
    assert session.add.call_count == 9
    assert session.flush.call_count == 3
    session.commit.assert_called_once()
