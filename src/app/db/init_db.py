"""Base.metadata 기반으로 테이블을 생성한다.

실행:
    python -m app.db.init_db   (--app-dir src 환경 또는 src가 PYTHONPATH에 있을 때)
"""

from app.db.base import Base
from app.db.session import engine

# Base.metadata에 모델을 등록하기 위해 import가 필요하다.
from app.db import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("tables created")
