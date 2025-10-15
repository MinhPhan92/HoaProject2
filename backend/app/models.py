from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Contract(Base):
    __tablename__ = "contract"

    ContractID: Mapped[int] = mapped_column("contractid", Integer, primary_key=True, index=True)
    CustomerID: Mapped[int] = mapped_column("customerid", Integer, ForeignKey("customer.customerid"), nullable=False)
    StartDate: Mapped[date | None] = mapped_column("startdate", Date, nullable=True)
    EndDate: Mapped[date | None] = mapped_column("enddate", Date, nullable=True)
    TotalAmount: Mapped[float | None] = mapped_column("totalamount", Numeric(15, 2), nullable=True)
    Status: Mapped[str | None] = mapped_column("status", String(100), nullable=True)
    Notes: Mapped[str | None] = mapped_column("notes", String(200), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="contracts")
    contract_cars: Mapped[list["ContractCar"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    payments: Mapped[list["ContractPayment"]] = relationship(back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "enddate IS NULL OR startdate IS NULL OR enddate >= startdate",
            name="ck_contract_date_range",
        ),
    )


class Customer(Base):
    __tablename__ = "customer"

    CustomerID: Mapped[int] = mapped_column("customerid", Integer, primary_key=True, index=True)
    FullName: Mapped[str] = mapped_column("fullname", String(100))
    Phone: Mapped[str | None] = mapped_column("phone", String(15), nullable=True)
    Email: Mapped[str | None] = mapped_column("email", String(100), nullable=True)
    Address: Mapped[str | None] = mapped_column("address", String(200), nullable=True)
    CitizenID: Mapped[str | None] = mapped_column("citizenid", String(12), nullable=True)
    RegistrationDate: Mapped[date | None] = mapped_column(
        "registrationdate", Date, server_default=text("CURRENT_DATE"), nullable=True
    )
    IsDeleted: Mapped[bool | None] = mapped_column("isdeleted", Boolean, server_default=text("FALSE"))

    contracts: Mapped[list["Contract"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class Car(Base):
    __tablename__ = "car"

    CarID: Mapped[int] = mapped_column("carid", Integer, primary_key=True, index=True)
    LicensePlate: Mapped[str] = mapped_column("licenseplate", String(20))
    DailyRate: Mapped[float | None] = mapped_column("dailyrate", Numeric(15, 2), nullable=True)
    HourlyRate: Mapped[float | None] = mapped_column("hourlyrate", Numeric(15, 2), nullable=True)
    Status: Mapped[str | None] = mapped_column("status", String(100), nullable=True)

    contract_cars: Mapped[list["ContractCar"]] = relationship(back_populates="car")


class ContractCar(Base):
    __tablename__ = "contractcar"

    ContractCarID: Mapped[int] = mapped_column("contractcarid", Integer, primary_key=True, index=True)
    ContractID: Mapped[int] = mapped_column("contractid", Integer, ForeignKey("contract.contractid"))
    CarID: Mapped[int] = mapped_column("carid", Integer, ForeignKey("car.carid"))
    Amount: Mapped[float | None] = mapped_column("amount", Numeric(15, 2), nullable=True)
    ReturnMileage: Mapped[int | None] = mapped_column("returnmileage", Integer, nullable=True)
    CarCondition: Mapped[str | None] = mapped_column("carcondition", String(100), nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="contract_cars")
    car: Mapped["Car"] = relationship(back_populates="contract_cars")


class ContractPayment(Base):
    __tablename__ = "contractpayment"

    PaymentID: Mapped[int] = mapped_column("paymentid", Integer, primary_key=True, index=True)
    ContractID: Mapped[int] = mapped_column("contractid", Integer, ForeignKey("contract.contractid"))
    PaymentMethod: Mapped[str | None] = mapped_column("paymentmethod", String(100), nullable=True)
    Amount: Mapped[float | None] = mapped_column("amount", Numeric(15, 2), nullable=True)
    PaymentDate: Mapped[date | None] = mapped_column("paymentdate", Date, nullable=True)
    Notes: Mapped[str | None] = mapped_column("notes", String(200), nullable=True)
    PaymentType: Mapped[int | None] = mapped_column("paymenttype", Integer, nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="payments")


class Surcharge(Base):
    __tablename__ = "surcharge"

    SurchargeID: Mapped[int] = mapped_column("surchargeid", Integer, primary_key=True, index=True)
    SurchargeName: Mapped[str | None] = mapped_column("surchargename", String(100), nullable=True)
    UnitPrice: Mapped[float | None] = mapped_column("unitprice", Numeric(15, 2), nullable=True)
    Description: Mapped[str | None] = mapped_column("description", String(200), nullable=True)


class ContractSurcharge(Base):
    __tablename__ = "contractsurcharge"

    ContractID: Mapped[int] = mapped_column("contractid", Integer, ForeignKey("contract.contractid"), primary_key=True)
    SurchargeID: Mapped[int] = mapped_column("surchargeid", Integer, ForeignKey("surcharge.surchargeid"), primary_key=True)
    UnitPrice: Mapped[float | None] = mapped_column("unitprice", Numeric(15, 2), nullable=True)
    Quantity: Mapped[int | None] = mapped_column("quantity", Integer, nullable=True)


class DeliveryReceipt(Base):
    __tablename__ = "deliveryreceipt"

    DeliveryID: Mapped[int] = mapped_column("deliveryid", Integer, primary_key=True, index=True)
    ContractID: Mapped[int] = mapped_column("contractid", Integer, ForeignKey("contract.contractid"))
    DeliveryEmployeeID: Mapped[int | None] = mapped_column("deliveryemployeeid", Integer, nullable=True)
    ReceiverEmployeeID: Mapped[int | None] = mapped_column("receiveremployeeid", Integer, nullable=True)
    DeliveryDate: Mapped[date | None] = mapped_column("deliverydate", Date, nullable=True)
    CarConditionAtDelivery: Mapped[str | None] = mapped_column("carconditionatdelivery", String(200), nullable=True)
    Notes: Mapped[str | None] = mapped_column("notes", String(200), nullable=True)


class ReturnReceipt(Base):
    __tablename__ = "returnreceipt"

    ReturnID: Mapped[int] = mapped_column("returnid", Integer, primary_key=True, index=True)
    ContractID: Mapped[int] = mapped_column("contractid", Integer, ForeignKey("contract.contractid"))
    ReceiverEmployeeID: Mapped[int | None] = mapped_column("receiveremployeeid", Integer, nullable=True)
    ReceiverBranchID: Mapped[int | None] = mapped_column("receiverbranchid", Integer, nullable=True)
    ReturnDate: Mapped[date | None] = mapped_column("returndate", Date, nullable=True)
    Notes: Mapped[str | None] = mapped_column("notes", String(200), nullable=True)
