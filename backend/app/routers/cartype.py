from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from pydantic import BaseModel


class CarTypeOut(BaseModel):
  type_id: int
  type_name: str | None = None

  class Config:
    from_attributes = True


router = APIRouter(prefix="/car-types", tags=["car-types"])


@router.get("/", response_model=List[CarTypeOut])
def list_car_types(db: Session = Depends(get_db)):
  # The current DB model file does not define a CarType table.
  # To keep the API working, return an empty list for now.
  return []


