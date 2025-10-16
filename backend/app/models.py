from datetime import date
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customer"

    CustomerID = Column("customerid", Integer, primary_key=True, index=True)
    FullName = Column("fullname", String(100), nullable=False)
    Phone = Column("phone", String(15), nullable=True)
    Email = Column("email", String(100), nullable=True)
    Address = Column("address", String(200), nullable=True)
    CitizenID = Column("citizenid", String(12), nullable=True)
    RegistrationDate = Column("registrationdate", Date, server_default=text("CURRENT_DATE"), nullable=True)
    IsDeleted = Column("isdeleted", Boolean, server_default=text("FALSE"))

    contracts = relationship("Contract", back_populates="customer")


class Branch(Base):
    __tablename__ = "branch"

    BranchID = Column("branchid", Integer, primary_key=True, index=True)
    BranchName = Column("branchname", String(100), nullable=False)
    Address = Column("address", String(200), nullable=True)
    Phone = Column("phone", String(15), nullable=True)


class Car(Base):
    __tablename__ = "car"

    CarID = Column("carid", Integer, primary_key=True, index=True)
    LicensePlate = Column("licenseplate", String(20), nullable=False)
    DailyRate = Column("dailyrate", Numeric(15, 2), nullable=True)
    HourlyRate = Column("hourlyrate", Numeric(15, 2), nullable=True)
    Status = Column("status", String(100), nullable=True)

    contract_cars = relationship("ContractCar", back_populates="car")


class Contract(Base):
    __tablename__ = "contract"

    ContractID = Column("contractid", Integer, primary_key=True, index=True)
    CustomerID = Column("customerid", Integer, ForeignKey("customer.customerid"))
    StartDate = Column("startdate", Date, nullable=True)
    EndDate = Column("enddate", Date, nullable=True)
    TotalAmount = Column("totalamount", Numeric(15, 2), nullable=True)
    Status = Column("status", String(100), nullable=True)
    Notes = Column("notes", String(200), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "enddate IS NULL OR startdate IS NULL OR enddate >= startdate",
            name="ck_contract_date_range",
        ),
    )

    customer = relationship("Customer", back_populates="contracts")
    contract_cars = relationship("ContractCar", back_populates="contract")
    payments = relationship("ContractPayment", back_populates="contract")


class ContractCar(Base):
    __tablename__ = "contractcar"

    ContractCarID = Column("contractcarid", Integer, primary_key=True, index=True)
    ContractID = Column("contractid", Integer, ForeignKey("contract.contractid"))
    CarID = Column("carid", Integer, ForeignKey("car.carid"))
    Amount = Column("amount", Numeric(15, 2), nullable=True)
    ReturnMileage = Column("returnmileage", Integer, nullable=True)
    CarCondition = Column("carcondition", String(100), nullable=True)

    contract = relationship("Contract", back_populates="contract_cars")
    car = relationship("Car", back_populates="contract_cars")


class ContractPayment(Base):
    __tablename__ = "contractpayment"

    PaymentID = Column("paymentid", Integer, primary_key=True, index=True)
    ContractID = Column("contractid", Integer, ForeignKey("contract.contractid"))
    PaymentMethod = Column("paymentmethod", String(100), nullable=True)
    Amount = Column("amount", Numeric(15, 2), nullable=True)
    PaymentDate = Column("paymentdate", Date, nullable=True)
    Notes = Column("notes", String(200), nullable=True)
    PaymentType = Column("paymenttype", Integer, nullable=True)

    contract = relationship("Contract", back_populates="payments")


class Surcharge(Base):
    __tablename__ = "surcharge"

    SurchargeID = Column("surchargeid", Integer, primary_key=True, index=True)
    SurchargeName = Column("surchargename", String(100), nullable=True)
    UnitPrice = Column("unitprice", Numeric(15, 2), nullable=True)
    Description = Column("description", String(200), nullable=True)


class ContractSurcharge(Base):
    __tablename__ = "contractsurcharge"

    ContractID = Column("contractid", Integer, ForeignKey("contract.contractid"), primary_key=True)
    SurchargeID = Column("surchargeid", Integer, ForeignKey("surcharge.surchargeid"), primary_key=True)
    UnitPrice = Column("unitprice", Numeric(15, 2), nullable=True)
    Quantity = Column("quantity", Integer, nullable=True)


class DeliveryReceipt(Base):
    __tablename__ = "deliveryreceipt"

    DeliveryID = Column("deliveryid", Integer, primary_key=True, index=True)
    ContractID = Column("contractid", Integer, ForeignKey("contract.contractid"))
    DeliveryEmployeeID = Column("deliveryemployeeid", Integer, nullable=True)
    ReceiverEmployeeID = Column("receiveremployeeid", Integer, nullable=True)
    DeliveryDate = Column("deliverydate", Date, nullable=True)
    CarConditionAtDelivery = Column("carconditionatdelivery", String(200), nullable=True)
    Notes = Column("notes", String(200), nullable=True)


class ReturnReceipt(Base):
    __tablename__ = "returnreceipt"

    ReturnID = Column("returnid", Integer, primary_key=True, index=True)
    ContractID = Column("contractid", Integer, ForeignKey("contract.contractid"))
    ReceiverEmployeeID = Column("receiveremployeeid", Integer, nullable=True)
    ReceiverBranchID = Column("receiverbranchid", Integer, nullable=True)
    ReturnDate = Column("returndate", Date, nullable=True)
    Notes = Column("notes", String(200), nullable=True)