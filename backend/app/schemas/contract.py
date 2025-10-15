from datetime import date
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class ContractBase(BaseModel):
    customer_id: int = Field(..., alias="CustomerID")
    start_date: Optional[date] = Field(None, alias="StartDate")
    end_date: Optional[date] = Field(None, alias="EndDate")
    total_amount: Optional[Decimal] = Field(None, alias="TotalAmount")
    status: Optional[str] = Field(None, alias="Status")
    notes: Optional[str] = Field(None, alias="Notes")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ContractCarItem(BaseModel):
    car_id: int = Field(..., alias="CarID")
    daily_rate: Optional[Decimal] = Field(None, alias="DailyRate")
    amount: Optional[Decimal] = Field(None, alias="Amount")

    model_config = ConfigDict(populate_by_name=True)


class ContractSurchargeItem(BaseModel):
    surcharge_id: Optional[int] = Field(None, alias="SurchargeID")
    unit_price: Decimal = Field(..., alias="UnitPrice")
    quantity: int = Field(..., alias="Quantity")

    model_config = ConfigDict(populate_by_name=True)


class ContractCreate(ContractBase):
    cars: List[ContractCarItem] = Field(default_factory=list, alias="Cars")
    surcharges: List[ContractSurchargeItem] = Field(default_factory=list, alias="Surcharges")


class DeliveryReceiptIn(BaseModel):
    delivery_employee_id: Optional[int] = Field(None, alias="DeliveryEmployeeID")
    receiver_employee_id: Optional[int] = Field(None, alias="ReceiverEmployeeID")
    delivery_date: Optional[date] = Field(None, alias="DeliveryDate")
    car_condition_at_delivery: Optional[str] = Field(None, alias="CarConditionAtDelivery")
    notes: Optional[str] = Field(None, alias="Notes")

    model_config = ConfigDict(populate_by_name=True)


class ReturnReceiptIn(BaseModel):
    receiver_employee_id: Optional[int] = Field(None, alias="ReceiverEmployeeID")
    receiver_branch_id: Optional[int] = Field(None, alias="ReceiverBranchID")
    return_date: Optional[date] = Field(None, alias="ReturnDate")
    notes: Optional[str] = Field(None, alias="Notes")

    model_config = ConfigDict(populate_by_name=True)


class ContractUpdate(BaseModel):
    customer_id: Optional[int] = Field(None, alias="CustomerID")
    start_date: Optional[date] = Field(None, alias="StartDate")
    end_date: Optional[date] = Field(None, alias="EndDate")
    total_amount: Optional[Decimal] = Field(None, alias="TotalAmount")
    status: Optional[str] = Field(None, alias="Status")
    notes: Optional[str] = Field(None, alias="Notes")

    model_config = ConfigDict(populate_by_name=True)


class ContractRead(BaseModel):
    id: int = Field(..., alias="ContractID")
    customer_id: int = Field(..., alias="CustomerID")
    start_date: Optional[date] = Field(None, alias="StartDate")
    end_date: Optional[date] = Field(None, alias="EndDate")
    total_amount: Optional[Decimal] = Field(None, alias="TotalAmount")
    status: Optional[str] = Field(None, alias="Status")
    notes: Optional[str] = Field(None, alias="Notes")
    cars: List[ContractCarItem] = Field(default_factory=list, alias="Cars")
    surcharges: List[ContractSurchargeItem] = Field(default_factory=list, alias="Surcharges")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


