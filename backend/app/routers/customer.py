from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from ..database import get_db
from ..models import Customer
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class CustomerBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None
    register_date: Optional[date] = None
    is_deleted: Optional[bool] = False


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None
    register_date: Optional[date] = None
    is_deleted: Optional[bool] = None


class CustomerOut(CustomerBase):
    customer_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerOut])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by name/phone/email (icontains)"),
    include_deleted: bool = Query(False, description="Include soft-deleted customers"),
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if not include_deleted:
        query = query.filter(Customer.is_deleted == False)  # noqa: E712
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(like))
            | (Customer.email.ilike(like))
            | (Customer.phone.ilike(like))
        )
    customers = query.order_by(Customer.customer_id).offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        national_id=payload.national_id,
        register_date=payload.register_date,
        is_deleted=payload.is_deleted or False,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if payload.full_name is not None:
        customer.full_name = payload.full_name.strip()
    if payload.phone is not None:
        customer.phone = payload.phone
    if payload.email is not None:
        customer.email = payload.email
    if payload.address is not None:
        customer.address = payload.address
    if payload.national_id is not None:
        customer.national_id = payload.national_id
    if payload.register_date is not None:
        customer.register_date = payload.register_date
    if payload.is_deleted is not None:
        customer.is_deleted = payload.is_deleted

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    # Soft delete to preserve history
    customer.is_deleted = True
    db.add(customer)
    db.commit()
    return None


