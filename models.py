# models.py
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    surname: str
    fathers_name: str
    address: str
    tax_id: str


@dataclass
class RentalRestData:
    property_kind: str
    property_address: str
    agreement_date: str
    monthly_rent: str     
    dept_months: str
    total_dept: str
    other_bills: str
    caller_demand: str
    compliance_deadline: str
    comments: str