from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import UserAccount, Role
from pydantic import BaseModel


# ----- Pydantic Schemas -----
class UserBase(BaseModel):
    role_id: int
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    user_id: int
    role_id: int
    username: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Filter by username (icontains)"),
    role_id: Optional[int] = Query(None, description="Filter by role_id"),
    db: Session = Depends(get_db),
):
    query = db.query(UserAccount)
    if search:
        query = query.filter(UserAccount.username.ilike(f"%{search}%"))
    if role_id is not None:
        query = query.filter(UserAccount.role_id == role_id)
    users = query.order_by(UserAccount.user_id).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # ensure role exists
    role = db.query(Role).filter(Role.role_id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")

    # uniqueness check
    existing = db.query(UserAccount).filter(UserAccount.username == payload.username.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = UserAccount(
        role_id=payload.role_id,
        username=payload.username.strip(),
        password=payload.password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role_id is not None:
        # ensure role exists
        role = db.query(Role).filter(Role.role_id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
        user.role_id = payload.role_id

    if payload.username is not None:
        new_username = payload.username.strip()
        exists = (
            db.query(UserAccount)
            .filter(UserAccount.username == new_username, UserAccount.user_id != user_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user.username = new_username

    if payload.password is not None:
        user.password = payload.password

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return None


