from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from models import EmployeeCreate, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["Employees"])


def fix_id(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_or_404(employee_id: str, db: AsyncIOMotorDatabase) -> dict:
    doc = await db["employees"].find_one({"employee_id": employee_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Employee not found")
    return doc


async def enrich(emp: dict, db: AsyncIOMotorDatabase) -> dict:
    college = await db["colleges"].find_one({"college_id": emp.get("college_id")})
    emp["college_name"] = college["college_name"] if college else None
    dept = await db["departments"].find_one({"dept_id": emp.get("dept_id")})
    emp["dept_name"] = dept["dept_name"] if dept else None
    return emp


async def validate_refs(college_id: str, dept_id: str, db: AsyncIOMotorDatabase):
    """Validate college exists, dept exists, AND dept belongs to college."""
    if not await db["colleges"].find_one({"college_id": college_id}):
        raise HTTPException(status_code=404, detail="College not found")
    dept = await db["departments"].find_one({"dept_id": dept_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept["college_id"] != college_id:
        raise HTTPException(
            status_code=400,
            detail=f"Department '{dept_id}' does not belong to college '{college_id}'",
        )


# ── CREATE  POST /employees ───────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await validate_refs(employee.college_id, employee.dept_id, db)
    if await db["employees"].find_one({"employee_id": employee.employee_id}):
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    result = await db["employees"].insert_one(employee.dict())
    return {"message": "Employee created", "id": str(result.inserted_id)}


# ── READ ALL  GET /employees ──────────────────────────────────────────────────

@router.get("/")
async def list_employees(
    college_id: str = None,
    dept_id: str = None,
    designation: str = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    query = {}
    if college_id:
        query["college_id"] = college_id
    if dept_id:
        query["dept_id"] = dept_id
    if designation:
        query["designation"] = designation

    employees = []
    async for emp in db["employees"].find(query):
        emp = fix_id(emp)
        emp = await enrich(emp, db)
        employees.append(emp)
    return employees


# ── READ ONE  GET /employees/{employee_id} ───────────────────────────────────

@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    emp = fix_id(await get_or_404(employee_id, db))
    return await enrich(emp, db)


# ── UPDATE (full)  PUT /employees/{employee_id} ───────────────────────────────

@router.put("/{employee_id}")
async def replace_employee(
    employee_id: str,
    employee: EmployeeCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Full replacement — all fields required."""
    await get_or_404(employee_id, db)
    await validate_refs(employee.college_id, employee.dept_id, db)
    await db["employees"].update_one({"employee_id": employee_id}, {"$set": employee.dict()})
    return {"message": "Employee fully updated"}


# ── UPDATE (partial)  PATCH /employees/{employee_id} ──────────────────────────

@router.patch("/{employee_id}")
async def patch_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Partial update — send only the fields you want to change."""
    await get_or_404(employee_id, db)
    changes = {k: v for k, v in employee.dict().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    # Re-validate refs if either college or dept is changing
    existing = await db["employees"].find_one({"employee_id": employee_id})
    new_college = changes.get("college_id", existing["college_id"])
    new_dept    = changes.get("dept_id",    existing["dept_id"])
    if "college_id" in changes or "dept_id" in changes:
        await validate_refs(new_college, new_dept, db)

    await db["employees"].update_one({"employee_id": employee_id}, {"$set": changes})
    return {"message": "Employee partially updated", "updated_fields": list(changes.keys())}


# ── DELETE  DELETE /employees/{employee_id} ───────────────────────────────────

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    result = await db["employees"].delete_one({"employee_id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")