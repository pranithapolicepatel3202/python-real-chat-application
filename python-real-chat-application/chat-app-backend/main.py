import uvicorn
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import db
from ws_manager import manager
from schemas import WSRegister
from routers import users as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db_pool()
    yield
    await db.close_db_pool()


# Create app only once
app = FastAPI(
    title="Real-time Chat Backend (FastAPI)",
    lifespan=lifespan
)

# allow local dev frontend origins - adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routers
app.include_router(users_router.router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    registered_id = None
    try:
        data_text = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        try:
            payload = json.loads(data_text)
        except Exception:
            await websocket.send_text(json.dumps({"error": "invalid_json"}))
            await websocket.close()
            return

        if payload.get("type") != "register":
            await websocket.send_text(json.dumps({"error": "first_message_must_be_register"}))
            await websocket.close()
            return

        reg = WSRegister(**payload)
        user_id, name = await manager.register(websocket, reg.user_id, reg.name)
        registered_id = user_id

        await websocket.send_text(json.dumps({"type": "registered", "user_id": user_id, "name": name}))

        while True:
            try:
                msg = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                break

            try:
                payload = json.loads(msg)
            except Exception:
                continue

            await manager.handle_message(user_id, payload)

    except asyncio.TimeoutError:
        await websocket.send_text(json.dumps({"error": "register_timeout"}))
        await websocket.close()
    except WebSocketDisconnect:
        pass
    finally:
        if registered_id:
            await manager.unregister(registered_id)
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
