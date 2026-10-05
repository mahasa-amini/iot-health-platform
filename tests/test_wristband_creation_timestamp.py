import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
DATA_STORAGE_SRC = ROOT / "services" / "data-storage" / "src"
sys.path.insert(0, str(DATA_STORAGE_SRC))

from models import Base  # noqa: E402
from storage.local import LocalStorage  # noqa: E402
import storage.local as local_module  # noqa: E402


def test_create_wristband_returns_persisted_created_at(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    test_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    monkeypatch.setattr(
        local_module,
        "SessionLocal",
        test_session_local,
    )

    storage = LocalStorage()
    created = storage.create_wristband(999)

    with engine.connect() as connection:
        persisted = connection.execute(
            text(
                """
                SELECT created_at
                FROM WRISTBAND
                WHERE wristband_id = :wristband_id
                """
            ),
            {"wristband_id": 999},
        ).scalar_one()

    assert str(created["created_at"]) == str(persisted)
