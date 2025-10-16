from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Car
from pydantic import BaseModel


class CarOut(BaseModel):
    car_id: int
    license_plate: str
    daily_rate: Optional[float] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("/", response_model=List[CarOut])
def list_cars(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Filter by license plate/status (icontains)"),
    db: Session = Depends(get_db),
):
    query = db.query(Car)
    if search:
        like = f"%{search}%"
        query = query.filter((Car.LicensePlate.ilike(like)) | (Car.Status.ilike(like)))
    items = (
        query.order_by(Car.CarID)
        .offset(max(0, skip))
        .limit(max(1, min(500, limit)))
        .all()
    )
    # map attribute names to snake_case expected by frontend
    result: List[CarOut] = []
    for c in items:
        result.append(
            CarOut(
                car_id=c.CarID,
                license_plate=c.LicensePlate,
                daily_rate=float(c.DailyRate or 0),
                hourly_rate=float(c.HourlyRate or 0),
                status=c.Status,
            )
        )
    return result


@router.get("/{car_id}", response_model=CarOut)
def get_car(car_id: int, db: Session = Depends(get_db)):
    c = db.query(Car).filter(Car.CarID == car_id).first()
    if not c:
        # Return 404 in a RESTful handler by raising, but keep it simple here
        from fastapi import HTTPException, status as _status

        raise HTTPException(status_code=_status.HTTP_404_NOT_FOUND, detail="Car not found")
    return CarOut(
        car_id=c.CarID,
        license_plate=c.LicensePlate,
        daily_rate=float(c.DailyRate or 0),
        hourly_rate=float(c.HourlyRate or 0),
        status=c.Status,
    )


# Alias router exposing the same endpoints under /vehicles
router_alias = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router_alias.get("/", response_model=List[CarOut])
def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Filter by plate/status (icontains)"),
    db: Session = Depends(get_db),
):
    return list_cars(skip=skip, limit=limit, search=search, db=db)


@router_alias.get("/{vehicle_id}", response_model=CarOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    return get_car(car_id=vehicle_id, db=db)


