from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
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


@router.get("", response_model=List[ContractRead])
def list_contracts(db: Session = Depends(get_db)):
    result = db.execute(select(Contract)).scalars().all()
    # Auto-sync status to Completed if return receipt exists
    for c in result:
        rr = db.execute(select(ReturnReceipt).where(ReturnReceipt.ContractID == c.ContractID)).scalars().first()
        if rr and (c.Status or "").lower() != "completed":
            c.Status = "Completed"
            db.add(c)
    db.commit()
    reads: List[ContractRead] = []
    for c in result:
        reads.append(
            ContractRead(
                ContractID=c.ContractID,
                CustomerID=c.CustomerID,
                StartDate=c.StartDate,
                EndDate=c.EndDate,
                TotalAmount=c.TotalAmount,
                Status=c.Status,
                Notes=c.Notes,
                Cars=[
                    ContractCarItem(CarID=cc.CarID, DailyRate=cc.car.DailyRate, Amount=cc.Amount)
                    for cc in (c.contract_cars or [])
                ],
                Surcharges=[
                    ContractSurchargeItem(
                        SurchargeID=cs.SurchargeID, UnitPrice=cs.UnitPrice or 0, Quantity=cs.Quantity or 0
                    )
                    for cs in (db.execute(
                        select(ContractSurcharge).where(ContractSurcharge.ContractID == c.ContractID)
                    ).scalars().all())
                ],
            )
        )
    return reads


def _overlaps(start_a: date | None, end_a: date | None, start_b: date | None, end_b: date | None) -> bool:
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return not (end_a < start_b or end_b < start_a)


def _calc_days(start_d: date | None, end_d: date | None) -> int:
    if not start_d or not end_d:
        return 0
    delta = (end_d - start_d).days
    return max(0, delta or 0)


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    if not payload.cars:
        raise HTTPException(status_code=400, detail="Hợp đồng phải có ít nhất 1 xe")
    # Availability check for each requested car in date range
    for item in payload.cars:
        # Find overlapping contracts for this car
        overlapping = db.execute(
            select(Contract)
            .join(ContractCar, ContractCar.ContractID == Contract.ContractID)
            .where(
                and_(
                    ContractCar.CarID == item.car_id,
                    Contract.StartDate.is_not(None),
                    Contract.EndDate.is_not(None),
                    Contract.Status != "Cancelled",
                    # overlap where (start <= payload.end) and (end >= payload.start)
                    Contract.StartDate <= (payload.end_date or payload.start_date),
                    Contract.EndDate >= (payload.start_date or payload.end_date),
                )
            )
        ).scalars().first()
        if overlapping:
            raise HTTPException(
                status_code=400,
                detail=f"Xe {item.car_id} không khả dụng trong khoảng thời gian đã chọn",
            )

    new_contract = Contract(
        CustomerID=payload.customer_id,
        StartDate=payload.start_date,
        EndDate=payload.end_date,
        Status="Renting",
        Notes=payload.notes,
    )
    db.add(new_contract)
    db.flush()  # get ContractID

    # Attach cars and compute base amount
    total_amount = 0
    days = _calc_days(payload.start_date, payload.end_date)
    for item in payload.cars:
        car = db.get(Car, item.car_id)
        if not car:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy xe {item.car_id}")
        daily = float(item.daily_rate or car.DailyRate or 0)
        amount = float(days * daily)
        total_amount += amount
        db.add(ContractCar(ContractID=new_contract.ContractID, CarID=car.CarID, Amount=amount))
        # Update car status to Renting
        car.Status = "Renting"
        db.add(car)

    # Apply surcharges
    for s in payload.surcharges:
        unit = float(s.unit_price or 0)
        qty = int(s.quantity or 0)
        total_amount += unit * qty
        db.add(
            ContractSurcharge(
                ContractID=new_contract.ContractID,
                SurchargeID=s.surcharge_id if s.surcharge_id is not None else 0,
                UnitPrice=unit,
                Quantity=qty,
            )
        )

    new_contract.TotalAmount = total_amount
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    return ContractRead(
        ContractID=new_contract.ContractID,
        CustomerID=new_contract.CustomerID,
        StartDate=new_contract.StartDate,
        EndDate=new_contract.EndDate,
        TotalAmount=new_contract.TotalAmount,
        Status=new_contract.Status,
        Notes=new_contract.Notes,
        Cars=[
            ContractCarItem(CarID=cc.CarID, DailyRate=cc.car.DailyRate, Amount=cc.Amount)
            for cc in new_contract.contract_cars
        ],
        Surcharges=[
            ContractSurchargeItem(
                SurchargeID=cs.SurchargeID, UnitPrice=cs.UnitPrice or 0, Quantity=cs.Quantity or 0
            )
            for cs in db.execute(
                select(ContractSurcharge).where(ContractSurcharge.ContractID == new_contract.ContractID)
            ).scalars().all()
        ],
    )


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
    return ContractRead(
        ContractID=contract.ContractID,
        CustomerID=contract.CustomerID,
        StartDate=contract.StartDate,
        EndDate=contract.EndDate,
        TotalAmount=contract.TotalAmount,
        Status=contract.Status,
        Notes=contract.Notes,
        Cars=[
            ContractCarItem(CarID=cc.CarID, DailyRate=cc.car.DailyRate, Amount=cc.Amount)
            for cc in (contract.contract_cars or [])
        ],
        Surcharges=[
            ContractSurchargeItem(
                SurchargeID=cs.SurchargeID, UnitPrice=cs.UnitPrice or 0, Quantity=cs.Quantity or 0
            )
            for cs in db.execute(
                select(ContractSurcharge).where(ContractSurcharge.ContractID == contract.ContractID)
            ).scalars().all()
        ],
    )


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
    if payload.total_amount is not None:
        contract.TotalAmount = payload.total_amount
    if payload.status is not None:
        contract.Status = payload.status
    if payload.notes is not None:
        contract.Notes = payload.notes

    # If status set to Completed, ensure a ReturnReceipt exists (auto-create if missing).
    # If status set to Canceled, free cars.
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
        # Free all cars used by this contract
        for cc in contract.contract_cars or []:
            car = db.get(Car, cc.CarID)
            if car:
                car.Status = "Ready"
                db.add(car)
        contract.Status = "Completed"
    elif payload.status and payload.status.lower() in {"canceled", "cancelled"}:
        for cc in contract.contract_cars or []:
            car = db.get(Car, cc.CarID)
            if car:
                car.Status = "Ready"
                db.add(car)
        contract.Status = "Canceled"

    db.add(contract)
    db.commit()
    db.refresh(contract)

    return ContractRead(
        ContractID=contract.ContractID,
        CustomerID=contract.CustomerID,
        StartDate=contract.StartDate,
        EndDate=contract.EndDate,
        TotalAmount=contract.TotalAmount,
        Status=contract.Status,
        Notes=contract.Notes,
        Cars=[
            ContractCarItem(CarID=cc.CarID, DailyRate=cc.car.DailyRate, Amount=cc.Amount)
            for cc in (contract.contract_cars or [])
        ],
        Surcharges=[
            ContractSurchargeItem(
                SurchargeID=cs.SurchargeID, UnitPrice=cs.UnitPrice or 0, Quantity=cs.Quantity or 0
            )
            for cs in db.execute(
                select(ContractSurcharge).where(ContractSurcharge.ContractID == contract.ContractID)
            ).scalars().all()
        ],
    )


@router.post("/{contract_id}/payments", status_code=status.HTTP_201_CREATED)
def add_payment(contract_id: int, amount: float, method: str = "Cash", db: Session = Depends(get_db)):
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
    # Mark contract completed and free cars
    contract = db.get(Contract, contract_id)
    if contract:
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


