from fastapi import APIRouter
from typing import List

import db
from schemas import UserInfo

router = APIRouter()


@router.get("/online-users", response_model=List[UserInfo])
async def list_online_users():
    users = await db.get_online_users_from_db()
    # ensure returned keys conform to UserInfo
    return users


@router.get("/health")
async def health():
    return {"status": "ok"}
