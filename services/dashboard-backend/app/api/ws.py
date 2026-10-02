from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.patient_vital_stream import patient_vital_stream

router = APIRouter()

@router.websocket("/patients/{patient_id}/vitals")
async def patient_vitals_ws(websocket: WebSocket, patient_id: int):
    await websocket.accept()
    print(f"[WS] connected: patient {patient_id}")

    try:
        async for event in patient_vital_stream.subscribe(patient_id):
            await websocket.send_json(event)

    except WebSocketDisconnect:
        print(f"[WS] disconnected: patient {patient_id}")
