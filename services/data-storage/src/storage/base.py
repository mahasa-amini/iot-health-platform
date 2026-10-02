from abc import ABC, abstractmethod
from sqlalchemy.orm import declarative_base

#  SQLAlchemy Base (برای ساخت جدول‌ها از روی models.py)
Base = declarative_base()


#  Interface برای Storage Backendها (Local / Cloud)
class StorageBackend(ABC):

    @abstractmethod
    def save_vital(self, assignment_id: int, data: dict) -> None:
        """Save one vital record for a given active assignment."""
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, assignment_id: int):
        """Return the latest vital record for an assignment."""
        raise NotImplementedError

    @abstractmethod
    def get_history(self, assignment_id: int, start=None, end=None):
        """Return a list of vital records for an assignment in a time range."""
        raise NotImplementedError

    @abstractmethod
    def unassign_wristband(self, wristband_id: int) -> bool:
        """
        End the active assignment for a wristband.
        Returns True if an assignment was closed.
        """
        raise NotImplementedError
