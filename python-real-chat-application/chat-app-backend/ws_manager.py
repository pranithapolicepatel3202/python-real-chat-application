import json
import uuid
from typing import Dict, Optional, Set, Tuple, List
from fastapi import WebSocket
from asyncio import Lock

import db


# Represents a connected user
class Connection:
    def __init__(self, user_id: str, name: str, websocket: WebSocket):
        self.user_id = user_id
        self.name = name
        self.ws = websocket


class WebSocketManager:
    def __init__(self):
        # user_id -> Connection
        self.active: Dict[str, Connection] = {}
        # set of active chat pairs stored as frozenset({u1,u2})
        self.active_chats: Set[frozenset] = set()
        self.lock = Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    async def register(self, websocket: WebSocket, user_id: Optional[str], name: Optional[str]) -> Tuple[str, str]:
        """
        Ensure user_id and name. Save connection and DB state.
        Returns (user_id, name)
        """
        if not user_id:
            user_id = str(uuid.uuid4())
        if not name:
            name = f"anon-{user_id[:8]}"

        conn = Connection(user_id=user_id, name=name, websocket=websocket)
        async with self.lock:
            self.active[user_id] = conn
        # persist to DB (mark connected)
        await db.set_user_connected(user_id, name, connected=True)
        # broadcast presence
        await self.broadcast_presence()
        return user_id, name

    async def unregister(self, user_id: str):
        async with self.lock:
            if user_id in self.active:
                del self.active[user_id]
        # mark disconnected in DB
        await db.set_user_disconnected(user_id)
        # remove any active chats involving user
        to_remove = [pair for pair in self.active_chats if user_id in pair]
        for pair in to_remove:
            self.active_chats.discard(pair)
            # notify other peer
            other = next(iter(pair - {user_id}))
            await self.safe_send_json_to_user(other, {"type": "chat_ended", "pair": list(pair)})
        # broadcast updated presence
        await self.broadcast_presence()

    async def broadcast_presence(self):
        users = await db.get_online_users_from_db()
        payload = {"type": "presence", "users": users}
        # send to all active websockets
        async with self.lock:
            conns = list(self.active.values())
        for c in conns:
            await self._safe_send_json(c.ws, payload)

    async def _safe_send_json(self, websocket: WebSocket, payload):
        try:
            await websocket.send_text(json.dumps(payload, default=str))
        except Exception:
            # ignore send errors — caller will handle cleanup if necessary
            pass

    async def send_to_user(self, user_id: str, payload: dict) -> bool:
        """
        Return True if user connected and send succeeded (best-effort).
        """
        async with self.lock:
            conn = self.active.get(user_id)
        if not conn:
            return False
        try:
            await conn.ws.send_text(json.dumps(payload, default=str))
            return True
        except Exception:
            return False

    async def safe_send_json_to_user(self, user_id: str, payload: dict):
        async with self.lock:
            conn = self.active.get(user_id)
        if conn:
            try:
                await conn.ws.send_text(json.dumps(payload, default=str))
            except Exception:
                pass

    async def handle_message(self, from_user: str, raw: dict):
        t = raw.get("type")
        if t == "start_chat":
            target = raw.get("target_id")
            if not target:
                return
            pair = frozenset({from_user, target})
            # ensure single chat per pair
            if pair in self.active_chats:
                # already active — notify requester
                await self.send_to_user(from_user, {"type": "chat_started", "pair": list(pair)})
                return
            self.active_chats.add(pair)
            # notify both parties if connected
            await self.safe_send_json_to_user(from_user, {"type": "chat_started", "pair": list(pair)})
            await self.safe_send_json_to_user(target, {"type": "chat_started", "pair": list(pair)})
        elif t == "end_chat":
            target = raw.get("target_id")
            if not target:
                return
            pair = frozenset({from_user, target})
            if pair in self.active_chats:
                self.active_chats.discard(pair)
                await self.safe_send_json_to_user(from_user, {"type": "chat_ended", "pair": list(pair)})
                await self.safe_send_json_to_user(target, {"type": "chat_ended", "pair": list(pair)})
        elif t == "message":
            to = raw.get("to")
            content = raw.get("content")
            if not to or content is None:
                return

            message_payload = {
                "type": "message",
                "from": from_user,
                "content": content
            }

            # Send to recipient
            await self.safe_send_json_to_user(to, message_payload)

            # Echo back to sender so they also see it in their chat window
            await self.safe_send_json_to_user(from_user, message_payload)

        # ignore unknown types; you can extend


# single instance
manager = WebSocketManager()
