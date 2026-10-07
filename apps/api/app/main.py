from typing import Literal

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ConnectionReady(BaseModel):
    version: Literal[1] = 1
    type: Literal["connection.ready"] = "connection.ready"
    payload: dict[str, object] = Field(default_factory=dict)


app = FastAPI(title="Kvartalno Kare API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(ConnectionReady().model_dump())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
