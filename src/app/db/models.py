from datetime import date

from sqlalchemy import Date, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PricePrediction(Base):
    """모델이 예측한 도매가 결과.

    한 번 예측할 때 기준일(base_date, 전일)을 바탕으로
    오늘 ~ 오늘+6일까지의 대상일(target_date)별 예측가를 산출하며,
    대상일 하나당 한 행으로 적재한다.
    """

    __tablename__ = "price_predictions"
    __table_args__ = (
        UniqueConstraint("base_date", "target_date", name="uq_prediction_base_target"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    base_date: Mapped[date] = mapped_column(Date, index=True)
    target_date: Mapped[date] = mapped_column(Date, index=True)
    predicted_price: Mapped[float] = mapped_column(Numeric(12, 2))
    # 직전 대상일 예측가 대비 가격 차이
    price_diff: Mapped[float] = mapped_column(Numeric(12, 2))


class ActualPrice(Base):
    """API로 수집한 전일자 실도매가."""

    __tablename__ = "actual_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    actual_price: Mapped[float] = mapped_column(Numeric(12, 2))
