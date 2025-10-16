from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from ..database import get_db
from ..models import Employee, Role, Branch
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class EmployeeBase(BaseModel):
    full_name: str
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    salary: Optional[float] = None
    role_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_deleted: Optional[bool] = False


class EmployeeCreate(EmployeeBase):
    role_id: int
    branch_id: int


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    salary: Optional[float] = None
    role_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_deleted: Optional[bool] = None


class EmployeeOut(EmployeeBase):
    employee_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=List[EmployeeOut])
def list_employees(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by name/email/phone (icontains)"),
    role_id: Optional[int] = Query(None, description="Filter by role_id"),
    branch_id: Optional[int] = Query(None, description="Filter by branch_id"),
    include_deleted: bool = Query(False, description="Include soft-deleted employees"),
    db: Session = Depends(get_db),
):
    query = db.query(Employee)
    if not include_deleted:
        query = query.filter(Employee.is_deleted == False)  # noqa: E712
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(like))
            | (Employee.email.ilike(like))
            | (Employee.phone.ilike(like))
        )
    if role_id is not None:
        query = query.filter(Employee.role_id == role_id)
    if branch_id is not None:
        query = query.filter(Employee.branch_id == branch_id)
    employees = query.order_by(Employee.employee_id).offset(skip).limit(limit).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # Ensure role and branch exist
    role = db.query(Role).filter(Role.role_id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
    branch = db.query(Branch).filter(Branch.branch_id == payload.branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch does not exist")

    employee = Employee(
        full_name=payload.full_name.strip(),
        birth_date=payload.birth_date,
        gender=payload.gender,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        salary=payload.salary,
        role_id=payload.role_id,
        branch_id=payload.branch_id,
        is_deleted=payload.is_deleted or False,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if payload.role_id is not None:
        role = db.query(Role).filter(Role.role_id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
        employee.role_id = payload.role_id

    if payload.branch_id is not None:
        branch = db.query(Branch).filter(Branch.branch_id == payload.branch_id).first()
        if not branch:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch does not exist")
        employee.branch_id = payload.branch_id

    if payload.full_name is not None:
        employee.full_name = payload.full_name.strip()
    if payload.birth_date is not None:
        employee.birth_date = payload.birth_date
    if payload.gender is not None:
        employee.gender = payload.gender
    if payload.phone is not None:
        employee.phone = payload.phone
    if payload.email is not None:
        employee.email = payload.email
    if payload.address is not None:
        employee.address = payload.address
    if payload.salary is not None:
        employee.salary = payload.salary
    if payload.is_deleted is not None:
        employee.is_deleted = payload.is_deleted

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    # Soft delete to preserve history
    employee.is_deleted = True
    db.add(employee)
    db.commit()
    return None


