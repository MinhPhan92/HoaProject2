-- 1. Role
CREATE TABLE Role (
    RoleID SERIAL PRIMARY KEY,
    RoleName VARCHAR(50) NOT NULL
);

-- 2. UserAccount
CREATE TABLE UserAccount (
    UserID SERIAL PRIMARY KEY,
    RoleID INT NOT NULL REFERENCES Role(RoleID),
    PasswordHash VARCHAR(100) NOT NULL
);

-- 3. Branch
CREATE TABLE Branch (
    BranchID SERIAL PRIMARY KEY,
    BranchName VARCHAR(100) NOT NULL,
    Address VARCHAR(200),
    Phone CHAR(15)
);

-- 4. Employee
CREATE TABLE Employee (
    EmployeeID SERIAL PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    BirthDate DATE,
    Gender VARCHAR(10),
    Phone CHAR(15),
    Email VARCHAR(100),
    Address VARCHAR(200),
    Salary DECIMAL(15,2),
    RoleID INT REFERENCES Role(RoleID),
    BranchID INT REFERENCES Branch(BranchID),
    IsDeleted BOOLEAN DEFAULT FALSE
);

-- 5. Customer
CREATE TABLE Customer (
    CustomerID SERIAL PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    Phone CHAR(15),
    Email VARCHAR(100),
    Address VARCHAR(200),
    CitizenID CHAR(12),
    RegistrationDate DATE DEFAULT CURRENT_DATE,
    IsDeleted BOOLEAN DEFAULT FALSE
);

-- 6. VehicleBrand
CREATE TABLE VehicleBrand (
    BrandID SERIAL PRIMARY KEY,
    BrandName VARCHAR(100) NOT NULL
);

-- 7. VehicleType
CREATE TABLE VehicleType (
    TypeID SERIAL PRIMARY KEY,
    TypeName VARCHAR(100),
    Description VARCHAR(200),
    RentalPrice DECIMAL(15,2)
);

-- 8. Vehicle
CREATE TABLE Vehicle (
    CarID SERIAL PRIMARY KEY,
    LicensePlate VARCHAR(20) UNIQUE NOT NULL,
    Color VARCHAR(50),
    ManufactureYear INT,
    Status VARCHAR(100),
    TypeID INT REFERENCES CarType(TypeID),
    BrandID INT REFERENCES CarBrand(BrandID),
    OwnerBranchID INT REFERENCES Branch(BranchID),
    IsDeleted BOOLEAN DEFAULT FALSE,
    Odometer FLOAT,
    DailyRate DECIMAL(15,2),
    HourlyRate DECIMAL(15,2)
);

-- 9. Contract
CREATE TABLE Contract (
    ContractID SERIAL PRIMARY KEY,
    CustomerID INT NOT NULL REFERENCES Customer(CustomerID),
    StartDate DATE,
    EndDate DATE,
    TotalAmount DECIMAL(15,2),
    Status VARCHAR(100),
    Notes VARCHAR(200)
);

-- 10. ContractVehicle
CREATE TABLE ContractVehicle (
    ContractVehicleID SERIAL PRIMARY KEY,
    ContractID INT NOT NULL REFERENCES Contract(ContractID),
    VehicleID INT REFERENCES Vehicle(VehicleID),
    Amount DECIMAL(15,2),
    ReturnMileage INT,
    VehicleCondition VARCHAR(100)
);

-- 11. ContractPayment
CREATE TABLE ContractPayment (
    PaymentID SERIAL PRIMARY KEY,
    ContractID INT NOT NULL REFERENCES Contract(ContractID),
    PaymentMethod VARCHAR(100),
    Amount DECIMAL(15,2),
    PaymentDate DATE DEFAULT CURRENT_DATE,
    Notes VARCHAR(200),
    PaymentType INT
);

-- 12. DeliveryReceipt
CREATE TABLE DeliveryReceipt (
    DeliveryID SERIAL PRIMARY KEY,
    ContractID INT NOT NULL REFERENCES Contract(ContractID),
    DeliveryEmployeeID INT REFERENCES Employee(EmployeeID),
    ReceiverEmployeeID INT REFERENCES Employee(EmployeeID),
    DeliveryDate DATE,
    VehicleConditionAtDelivery VARCHAR(200),
    Notes VARCHAR(200)
);

-- 13. ReturnReceipt
CREATE TABLE ReturnReceipt (
    ReturnID SERIAL PRIMARY KEY,
    ContractID INT NOT NULL REFERENCES Contract(ContractID),
    ReceiverEmployeeID INT REFERENCES Employee(EmployeeID),
    ReceiverBranchID INT REFERENCES Branch(BranchID),
    ReturnDate DATE,
    Notes VARCHAR(200)
);

-- 14. Surcharge
CREATE TABLE Surcharge (
    SurchargeID SERIAL PRIMARY KEY,
    SurchargeName VARCHAR(100),
    UnitPrice DECIMAL(15,2),
    Description VARCHAR(200)
);

-- 15. ContractSurcharge
CREATE TABLE ContractSurcharge (
    ContractID INT NOT NULL REFERENCES Contract(ContractID),
    SurchargeID INT REFERENCES Surcharge(SurchargeID),
    UnitPrice DECIMAL(15,2),
    Quantity INT,
    PRIMARY KEY (ContractID, SurchargeID)
);

















-- 1. Role
INSERT INTO Role (RoleName) VALUES
('Administrator'),
('Manager'),
('Staff'),
('Customer');

-- 2. UserAccount
INSERT INTO UserAccount (RoleID, PasswordHash) VALUES
(1, 'admin123'),
(2, 'manager123'),
(3, 'staff123'),
(4, 'customer123');

-- 3. Branch
INSERT INTO Branch (BranchName, Address, Phone) VALUES
('Downtown Branch', '123 Main St, City Center', '0123456789'),
('Airport Branch', '456 Airport Rd, City Outskirts', '0987654321');

-- 4. Employee
INSERT INTO Employee (FullName, BirthDate, Gender, Phone, Email, Address, Salary, RoleID, BranchID)
VALUES
('John Smith', '1988-05-14', 'Male', '0901111222', 'john.smith@carrental.com', '45 Green St, City Center', 1500.00, 2, 1),
('Emily Johnson', '1992-09-10', 'Female', '0903333444', 'emily.johnson@carrental.com', '22 Blue Rd, City Center', 1200.00, 3, 1),
('Michael Brown', '1990-12-25', 'Male', '0905555666', 'michael.brown@carrental.com', '88 Lake Ave, Airport District', 1300.00, 3, 2);

-- 5. Customer
INSERT INTO Customer (FullName, Phone, Email, Address, CitizenID)
VALUES
('Alice Walker', '0907777888', 'alice.walker@email.com', '12 Elm St, Downtown', '123456789012'),
('Robert Davis', '0909999000', 'robert.davis@email.com', '55 Hill Rd, Uptown', '098765432109');

-- 6. CarBrand
INSERT INTO CarBrand (BrandName) VALUES
('Toyota'),
('Honda'),
('Ford');

-- 7. CarType
INSERT INTO CarType (TypeName, Description, RentalPrice)
VALUES
('Sedan', 'Comfortable 4-seater for city driving', 50.00),
('SUV', 'Spacious 7-seater for long trips', 80.00),
('Truck', 'Heavy-duty cargo transport', 100.00);

-- 8. Car
INSERT INTO Car (LicensePlate, Color, ManufactureYear, Status, TypeID, BrandID, OwnerBranchID, Odometer, DailyRate, HourlyRate)
VALUES
('ABC-123', 'White', 2020, 'Available', 1, 1, 1, 35000, 50.00, 7.00),
('XYZ-789', 'Black', 2021, 'Available', 2, 2, 1, 25000, 80.00, 10.00),
('LMN-456', 'Silver', 2019, 'Rented', 3, 3, 2, 60000, 100.00, 15.00);

-- 9. Contract
INSERT INTO Contract (CustomerID, StartDate, EndDate, TotalAmount, Status, Notes)
VALUES
(1, '2025-10-10', '2025-10-14', 320.00, 'Active', 'Short-term rental'),
(2, '2025-10-05', '2025-10-15', 800.00, 'Completed', 'No issues reported');

-- 10. ContractCar
INSERT INTO ContractCar (ContractID, CarID, Amount, ReturnMileage, CarCondition)
VALUES
(1, 1, 200.00, 35500, 'Good condition'),
(1, 2, 120.00, 25200, 'Minor scratches'),
(2, 3, 800.00, 61000, 'Excellent');

-- 11. ContractPayment
INSERT INTO ContractPayment (ContractID, PaymentMethod, Amount, PaymentType, Notes)
VALUES
(1, 'Credit Card', 320.00, 1, 'Full payment upfront'),
(2, 'Cash', 800.00, 1, 'Paid at return');

-- 12. DeliveryReceipt
INSERT INTO DeliveryReceipt (ContractID, DeliveryEmployeeID, ReceiverEmployeeID, DeliveryDate, CarConditionAtDelivery, Notes)
VALUES
(1, 2, 3, '2025-10-10', 'Clean and full fuel', 'Delivered to customer on time'),
(2, 3, 2, '2025-10-05', 'Minor scratches noted', 'Pre-existing damage recorded');

-- 13. ReturnReceipt
INSERT INTO ReturnReceipt (ContractID, ReceiverEmployeeID, ReceiverBranchID, ReturnDate, Notes)
VALUES
(1, 3, 1, '2025-10-14', 'Returned without issue'),
(2, 2, 2, '2025-10-15', 'Returned in excellent condition');

-- 14. Surcharge
INSERT INTO Surcharge (SurchargeName, UnitPrice, Description)
VALUES
('Late Return Fee', 20.00, 'Applied per hour past due time'),
('Fuel Charge', 15.00, 'If fuel level is below full upon return'),
('Cleaning Fee', 10.00, 'For excessive dirt or stains');

-- 15. ContractSurcharge
INSERT INTO ContractSurcharge (ContractID, SurchargeID, UnitPrice, Quantity)
VALUES
(1, 1, 20.00, 1),
(1, 3, 10.00, 1),
(2, 2, 15.00, 1);


select * from Contract