from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class UserInfo(BaseModel):
    id: str
    name: str
    connected: bool
    last_seen: Optional[datetime]


class WSRegister(BaseModel):
    type: str = "register"
    user_id: Optional[str] = None
    name: Optional[str] = None


class WSStartChat(BaseModel):
    type: str = "start_chat"
    target_id: str


class WSEndChat(BaseModel):
    type: str = "end_chat"
    target_id: str


class WSMessage(BaseModel):
    type: str = "message"
    to: str
    content: str


# Generic outgoing messages
class WSPresence(BaseModel):
    type: str = "presence"
    users: List[UserInfo]


class WSRegistered(BaseModel):
    type: str = "registered"
    user_id: str
    name: str
