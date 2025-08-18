from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/connect")
async def connect_endpoint(request: Request):
    """Endpoint simple para que el frontend confirme conexión y el backend logee en terminal."""
    client_host = request.client.host if request.client else "unknown"
    try:
        body = await request.json()
    except Exception:
        body = {}
    print(f"[CONNECT] request from {client_host} - payload: {body}")
    return {"status": "ok", "message": "connected", "from": client_host}
