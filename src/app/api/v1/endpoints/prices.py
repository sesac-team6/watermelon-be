from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schema.price import PriceResponse

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]
TargetDate = Annotated[
    date,
    Query(alias="date", description="Start date in YYYY-MM-DD format"),
]


@router.get("", response_model=list[PriceResponse])
def get_weekly_prices(
    db: DatabaseSession,
    target_date: TargetDate,
) -> list[PriceResponse]:
    end_date = target_date + timedelta(days=7)
    result = db.execute(
        text(
            """
            SELECT id, "date", price
            FROM prices
            WHERE "date" >= :start_date
              AND "date" < :end_date
            ORDER BY "date" ASC, id ASC
            """
        ),
        {
            "start_date": target_date,
            "end_date": end_date,
        },
    )

    return [PriceResponse.model_validate(row) for row in result.mappings().all()]
