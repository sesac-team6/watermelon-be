from datetime import date

from pydantic import BaseModel


class PriceResponse(BaseModel):
    id: int
    date: date
    price: int
