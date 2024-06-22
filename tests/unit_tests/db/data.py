from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from tests.mocks import UUID_ID

DICT = {
    1: "one",
    2: "two",
    3: "three",
    4: UUID_ID,
}
DICT_JSON = "".join(('{"1": "one", "2": "two", "3": "three", "4": ', f'"{UUID_ID}"', "}"))


DICT_UUID = {
    1: "one",
    2: "two",
    3: "three",
    4: UUID_ID,
}
DICT_UUID_JSON = "".join(('{"1": "one", "2": "two", "3": "three", "4": ', f'"{UUID_ID}"', "}"))


class Department(Enum):
    HR = "HR"
    SALES = "SALES"
    IT = "IT"
    ENGINEERING = "ENGINEERING"


class Employee(BaseModel):
    """No nested objects, just native data types."""

    employee_id: int = 1
    name: str
    salary: float
    elected_benefits: bool


class ComplexEmployee(Employee):
    """Nested objects 'date' and 'Enum'."""

    employee_id: UUID = UUID_ID
    date_of_birth: date
    department: Department


FLAT_BASE_MODEL = Employee(
    name="Chris DeTuma",
    salary=123_000.00,
    elected_benefits=True,
)
FLAT_BASE_MODEL_EXPECTED_JSON = (
    '{"employee_id": 1, "name": "Chris DeTuma", "salary": 123000.0, "elected_benefits": true}'
)

FLAT_BASE_MODELS = [FLAT_BASE_MODEL, FLAT_BASE_MODEL]
FLAT_BASE_MODELS_EXPECTED_JSON = (
    '[{"employee_id": 1, "name": "Chris DeTuma", "salary": 123000.0, "elected_benefits": true}, '
    '{"employee_id": 1, "name": "Chris DeTuma", "salary": 123000.0, "elected_benefits": true}]'
)


NESTED_BASE_MODEL = ComplexEmployee(
    name="Chris DeTuma",
    date_of_birth="1998-04-02",
    salary=123_000.00,
    department="IT",
    elected_benefits=True,
)
NESTED_BASE_MODEL_EXPECTED_JSON = (
    '{"employee_id": '
    + f'"{UUID_ID}", '
    + '"name": "Chris DeTuma", "salary": 123000.0, "elected_benefits": true, '
    '"date_of_birth": "1998-04-02", "department": "IT"}'
)

NESTED_BASE_MODELS = [NESTED_BASE_MODEL, NESTED_BASE_MODEL]
NESTED_BASE_MODELS_EXPECTED_JSON = f"[{NESTED_BASE_MODEL_EXPECTED_JSON}, {NESTED_BASE_MODEL_EXPECTED_JSON}]"
