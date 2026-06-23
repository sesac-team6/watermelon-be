from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/ping")
def ping_database(db: DatabaseSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
