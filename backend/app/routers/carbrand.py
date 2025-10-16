from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import CarBrand
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class CarBrandBase(BaseModel):
    brand_name: str


class CarBrandCreate(CarBrandBase):
    pass


class CarBrandUpdate(BaseModel):
    brand_name: Optional[str] = None


class CarBrandOut(CarBrandBase):
    brand_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/car-brands", tags=["car-brands"])


@router.get("/", response_model=List[CarBrandOut])
def list_car_brands(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by brand name (icontains)"),
    db: Session = Depends(get_db),
):
    query = db.query(CarBrand)
    if search:
        query = query.filter(CarBrand.brand_name.ilike(f"%{search}%"))
    items = query.order_by(CarBrand.brand_id).offset(skip).limit(limit).all()
    return items


@router.get("/{brand_id}", response_model=CarBrandOut)
def get_car_brand(brand_id: int, db: Session = Depends(get_db)):
    item = db.query(CarBrand).filter(CarBrand.brand_id == brand_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car brand not found")
    return item


@router.post("/", response_model=CarBrandOut, status_code=status.HTTP_201_CREATED)
def create_car_brand(payload: CarBrandCreate, db: Session = Depends(get_db)):
    name = payload.brand_name.strip()
    exists = db.query(CarBrand).filter(CarBrand.brand_name == name).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Brand name already exists")
    item = CarBrand(brand_name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{brand_id}", response_model=CarBrandOut)
def update_car_brand(brand_id: int, payload: CarBrandUpdate, db: Session = Depends(get_db)):
    item = db.query(CarBrand).filter(CarBrand.brand_id == brand_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car brand not found")

    if payload.brand_name is not None:
        new_name = payload.brand_name.strip()
        exists = (
            db.query(CarBrand)
            .filter(CarBrand.brand_name == new_name, CarBrand.brand_id != brand_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Brand name already exists")
        item.brand_name = new_name

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car_brand(brand_id: int, db: Session = Depends(get_db)):
    item = db.query(CarBrand).filter(CarBrand.brand_id == brand_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car brand not found")
    db.delete(item)
    db.commit()
    return None


