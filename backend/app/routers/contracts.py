from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Car,
    Contract,
    ContractCar,
    ContractPayment,
    ContractSurcharge,
    DeliveryReceipt,
    ReturnReceipt,
)
from ..schemas.contract import (
    ContractCreate,
    ContractRead,
    ContractUpdate,
    ContractCarItem,
    ContractSurchargeItem,
    DeliveryReceiptIn,
    ReturnReceiptIn,
)


router = APIRouter(prefix="/contracts", tags=["contracts"])


def _contract_to_read(c: Contract, db: Session) -> ContractRead:
    cars = [
        ContractCarItem(CarID=cc.CarID, DailyRate=cc.car.DailyRate, Amount=cc.Amount)
        for cc in (c.contract_cars or [])
    ]
    surcharges = [
        ContractSurchargeItem(
            SurchargeID=cs.SurchargeID, UnitPrice=cs.UnitPrice or 0, Quantity=cs.Quantity or 0
        )
        for cs in db.execute(
            select(ContractSurcharge).where(ContractSurcharge.ContractID == c.ContractID)
        ).scalars().all()
    ]
    # Use field names (not aliases) when constructing pydantic models
    return ContractRead(
        id=c.ContractID,
        customer_id=c.CustomerID,
        start_date=c.StartDate,
        end_date=c.EndDate,
        total_amount=getattr(c, "TotalAmount", None),
        status=getattr(c, "Status", None),
        notes=getattr(c, "Notes", None),
        cars=cars,
        surcharges=surcharges,
    )


@router.get("", response_model=List[ContractRead])
def list_contracts(db: Session = Depends(get_db)):
    contracts = db.execute(select(Contract)).scalars().all()
    # Auto-sync status to Completed if return receipt exists
    changed = False
    for c in contracts:
        rr = db.execute(select(ReturnReceipt).where(ReturnReceipt.ContractID == c.ContractID)).scalars().first()
        if rr and (getattr(c, "Status", None) or "").lower() != "completed":
            c.Status = "Completed"
            db.add(c)
            changed = True
    if changed:
        db.commit()
    return [_contract_to_read(c, db) for c in contracts]


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    # Create contract
    new_contract = Contract(
        CustomerID=payload.customer_id,
        StartDate=payload.start_date,
        EndDate=payload.end_date,
        # Optional fields if present in model
        **({"TotalAmount": payload.total_amount} if hasattr(Contract, "TotalAmount") else {}),
        **({"Status": payload.status} if hasattr(Contract, "Status") else {}),
        **({"Notes": payload.notes} if hasattr(Contract, "Notes") else {}),
    )
    db.add(new_contract)
    db.flush()  # Have ContractID for relations

    # Add cars
    for item in payload.cars or []:
        db.add(
            ContractCar(
                ContractID=new_contract.ContractID,
                CarID=item.car_id,
                Amount=item.amount,
            )
        )
        car = db.get(Car, item.car_id)
        if car:
            car.Status = "Rented"
            db.add(car)

    # Add surcharges
    for s in payload.surcharges or []:
        db.add(
            ContractSurcharge(
                ContractID=new_contract.ContractID,
                SurchargeID=s.surcharge_id if s.surcharge_id is not None else 0,
                UnitPrice=s.unit_price,
                Quantity=s.quantity,
            )
        )

    db.commit()
    db.refresh(new_contract)
    return _contract_to_read(new_contract, db)


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    return _contract_to_read(contract, db)


@router.put("/{contract_id}", response_model=ContractRead)
def update_contract(contract_id: int, payload: ContractUpdate, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")

    if payload.customer_id is not None:
        contract.CustomerID = payload.customer_id
    if payload.start_date is not None:
        contract.StartDate = payload.start_date
    if payload.end_date is not None:
        contract.EndDate = payload.end_date
    if payload.total_amount is not None and hasattr(contract, "TotalAmount"):
        contract.TotalAmount = payload.total_amount
    if payload.status is not None and hasattr(contract, "Status"):
        contract.Status = payload.status
    if payload.notes is not None and hasattr(contract, "Notes"):
        contract.Notes = payload.notes

    # Status side-effects
    if payload.status and payload.status.lower() in {"completed", "returned", "done"}:
        existing_return = db.execute(
            select(ReturnReceipt).where(ReturnReceipt.ContractID == contract.ContractID)
        ).scalars().first()
        if not existing_return:
            db.add(
                ReturnReceipt(
                    ContractID=contract.ContractID,
                    ReturnDate=payload.end_date or contract.EndDate,
                    Notes="Auto-created on status update",
                )
            )
        for cc in contract.contract_cars or []:
            car = db.get(Car, cc.CarID)
            if car:
                car.Status = "Ready"
                db.add(car)
        if hasattr(contract, "Status"):
            contract.Status = "Completed"
    elif payload.status and payload.status.lower() in {"canceled", "cancelled"}:
        for cc in contract.contract_cars or []:
            car = db.get(Car, cc.CarID)
            if car:
                car.Status = "Ready"
                db.add(car)
        if hasattr(contract, "Status"):
            contract.Status = "Canceled"

    db.add(contract)
    db.commit()
    db.refresh(contract)
    return _contract_to_read(contract, db)


@router.post("/{contract_id}/payments", status_code=status.HTTP_201_CREATED)
def add_payment(
    contract_id: int,
    amount: float = Query(..., ge=0),
    method: str = Query("Cash"),
    db: Session = Depends(get_db),
):
    if not db.get(Contract, contract_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    pay = ContractPayment(ContractID=contract_id, Amount=amount, PaymentMethod=method)
    db.add(pay)
    db.commit()
    return {"PaymentID": pay.PaymentID}


@router.post("/{contract_id}/delivery", status_code=status.HTTP_201_CREATED)
def create_delivery(contract_id: int, body: DeliveryReceiptIn, db: Session = Depends(get_db)):
    if not db.get(Contract, contract_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    rec = DeliveryReceipt(
        ContractID=contract_id,
        DeliveryEmployeeID=body.delivery_employee_id,
        ReceiverEmployeeID=body.receiver_employee_id,
        DeliveryDate=body.delivery_date,
        CarConditionAtDelivery=body.car_condition_at_delivery,
        Notes=body.notes,
    )
    db.add(rec)
    db.commit()
    return {"DeliveryID": rec.DeliveryID}


@router.post("/{contract_id}/return", status_code=status.HTTP_201_CREATED)
def create_return(contract_id: int, body: ReturnReceiptIn, db: Session = Depends(get_db)):
    if not db.get(Contract, contract_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    rec = ReturnReceipt(
        ContractID=contract_id,
        ReceiverEmployeeID=body.receiver_employee_id,
        ReceiverBranchID=body.receiver_branch_id,
        ReturnDate=body.return_date,
        Notes=body.notes,
    )
    db.add(rec)
    contract = db.get(Contract, contract_id)
    if contract and hasattr(contract, "Status"):
        contract.Status = "Completed"
        for cc in contract.contract_cars or []:
            car = db.get(Car, cc.CarID)
            if car:
                car.Status = "Ready"
                db.add(car)
        db.add(contract)
    db.commit()
    return {"ReturnID": rec.ReturnID}


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    db.delete(contract)
    db.commit()
    return None


