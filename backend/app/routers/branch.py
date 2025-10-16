from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Branch
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class BranchBase(BaseModel):
    branch_name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class BranchOut(BranchBase):
    branch_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("/", response_model=List[BranchOut])
def list_branches(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by branch name (icontains)"),
    db: Session = Depends(get_db),
):
    query = db.query(Branch)
    if search:
        query = query.filter(Branch.branch_name.ilike(f"%{search}%"))
    branches = query.order_by(Branch.branch_id).offset(skip).limit(limit).all()
    return branches


@router.get("/{branch_id}", response_model=BranchOut)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = db.query(Branch).filter(Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch


@router.post("/", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db)):
    # Optional: uniqueness by name within address
    existing = (
        db.query(Branch)
        .filter(Branch.branch_name == payload.branch_name.strip())
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch name already exists")

    branch = Branch(
        branch_name=payload.branch_name.strip(),
        address=payload.address,
        phone=payload.phone,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.put("/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: int, payload: BranchUpdate, db: Session = Depends(get_db)):
    branch = db.query(Branch).filter(Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    if payload.branch_name is not None:
        new_name = payload.branch_name.strip()
        exists = (
            db.query(Branch)
            .filter(Branch.branch_name == new_name, Branch.branch_id != branch_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch name already exists")
        branch.branch_name = new_name

    if payload.address is not None:
        branch.address = payload.address

    if payload.phone is not None:
        branch.phone = payload.phone

    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = db.query(Branch).filter(Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    db.delete(branch)
    db.commit()
    return None


