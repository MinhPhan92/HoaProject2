from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Role
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class RoleBase(BaseModel):
    role_name: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None


class RoleOut(RoleBase):
    role_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleOut])
def list_roles(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by role name (icontains)"),
    db: Session = Depends(get_db),
):
    query = db.query(Role)
    if search:
        query = query.filter(Role.role_name.ilike(f"%{search}%"))
    roles = query.order_by(Role.role_id).offset(skip).limit(limit).all()
    return roles


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    # Optional uniqueness check by name
    existing = db.query(Role).filter(Role.role_name == payload.role_name.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")

    role = Role(role_name=payload.role_name.strip())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if payload.role_name is not None:
        new_name = payload.role_name.strip()
        # Uniqueness check when changing name
        exists = (
            db.query(Role)
            .filter(Role.role_name == new_name, Role.role_id != role_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")
        role.role_name = new_name

    # updated_at handled by model on update
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    db.delete(role)
    db.commit()
    return None


