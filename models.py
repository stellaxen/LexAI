# models.py
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    surname: str
    fathers_name: str
    address: str
    tax_id: str
