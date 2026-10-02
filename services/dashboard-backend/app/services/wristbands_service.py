from app.services.storage import Storage


def create_wristband(storage: Storage, wristband_id: int) -> dict:
    """
    Create wristband (business layer).
    """
    return storage.create_wristband(wristband_id)


def list_wristbands(storage: Storage) -> dict:
    """
    Return all wristbands (UI-ready).
    """
    return {"items": storage.list_wristbands()}


# def list_available_wristbands(storage: Storage) -> dict:
#     """
#     Return available wristbands (no active assignment).
#     """
#     return {"items": storage.list_available_wristbands()}


def unassign_wristband(storage: Storage, wristband_id: int) -> None:
    storage.unassign_wristband(wristband_id)
