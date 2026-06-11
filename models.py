from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId

# NOTE: *Update models have every field Optional so PATCH can send only the
# fields that should change — unset fields are excluded from the $set query.


# ── Utility ──────────────────────────────────────────────────────────────────

class PyObjectId(str):
    """Lets Pydantic accept MongoDB ObjectIds as plain strings."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return str(v)


# ── Department ────────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    dept_id: str = Field(..., example="CSE001")
    dept_name: str = Field(..., example="Computer Science")
    college_id: str = Field(..., example="CLG001")          # FK → College

    class Config:
        populate_by_name = True


class DepartmentUpdate(BaseModel):
    dept_name: Optional[str] = None
    college_id: Optional[str] = None

    class Config:
        populate_by_name = True


class DepartmentOut(DepartmentCreate):
    id: Optional[str] = Field(None, alias="_id")
    college_name: Optional[str] = None                      # populated on read

    class Config:
        populate_by_name = True


# ── College ───────────────────────────────────────────────────────────────────

class CollegeCreate(BaseModel):
    college_id: str = Field(..., example="CLG001")
    college_name: str = Field(..., example="MIT College of Engineering")
    location: str = Field(..., example="Hyderabad")
    established_year: int = Field(..., example=1990)

    class Config:
        populate_by_name = True


class CollegeUpdate(BaseModel):
    college_name: Optional[str] = None
    location: Optional[str] = None
    established_year: Optional[int] = None

    class Config:
        populate_by_name = True


class CollegeOut(CollegeCreate):
    id: Optional[str] = Field(None, alias="_id")
    departments: List[dict] = []                            # embedded on read

    class Config:
        populate_by_name = True


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_id: str = Field(..., example="STU2024001")
    student_name: str = Field(..., example="Ravi Kumar")
    email: str = Field(..., example="ravi.kumar@mit.edu")
    phone: Optional[str] = Field(None, example="9876543210")
    age: Optional[int] = Field(None, example=20)
    year_of_study: int = Field(..., example=2, ge=1, le=5)
    dept_id: str = Field(..., example="CSE001")             # FK → Department
    college_id: str = Field(..., example="CLG001")          # FK → College

    class Config:
        populate_by_name = True


class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=5)
    dept_id: Optional[str] = None
    college_id: Optional[str] = None

    class Config:
        populate_by_name = True


class StudentOut(StudentCreate):
    id: Optional[str] = Field(None, alias="_id")
    college_name: Optional[str] = None                      # populated on read
    dept_name: Optional[str] = None                         # populated on read

    class Config:
        populate_by_name = True


# ── Employee ──────────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    employee_id: str = Field(..., example="EMP001")
    employee_name: str = Field(..., example="Dr. Priya Sharma")
    email: str = Field(..., example="priya.sharma@mit.edu")
    phone: Optional[str] = Field(None, example="9123456789")
    designation: str = Field(..., example="Professor")
    salary: Optional[float] = Field(None, example=85000.0)
    dept_id: str = Field(..., example="CSE001")             # FK → Department
    college_id: str = Field(..., example="CLG001")          # FK → College

    class Config:
        populate_by_name = True


class EmployeeUpdate(BaseModel):
    employee_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    salary: Optional[float] = None
    dept_id: Optional[str] = None
    college_id: Optional[str] = None

    class Config:
        populate_by_name = True


class EmployeeOut(EmployeeCreate):
    id: Optional[str] = Field(None, alias="_id")
    college_name: Optional[str] = None                      # populated on read
    dept_name: Optional[str] = None                         # populated on read

    class Config:
        populate_by_name = True