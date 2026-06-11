from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from models import DepartmentCreate, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["Departments"])


def fix_id(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_or_404(dept_id: str, db: AsyncIOMotorDatabase) -> dict:
    doc = await db["departments"].find_one({"dept_id": dept_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Department not found")
    return doc


async def enrich(dept: dict, db: AsyncIOMotorDatabase) -> dict:
    college = await db["colleges"].find_one({"college_id": dept.get("college_id")})
    dept["college_name"] = college["college_name"] if college else None
    return dept


async def validate_college(college_id: str, db: AsyncIOMotorDatabase):
    if not await db["colleges"].find_one({"college_id": college_id}):
        raise HTTPException(status_code=404, detail="College not found")


# ── CREATE  POST /departments ─────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_department(
    dept: DepartmentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await validate_college(dept.college_id, db)
    if await db["departments"].find_one({"dept_id": dept.dept_id}):
        raise HTTPException(status_code=400, detail="Department ID already exists")
    result = await db["departments"].insert_one(dept.dict())
    return {"message": "Department created", "id": str(result.inserted_id)}


# ── READ ALL  GET /departments ────────────────────────────────────────────────

@router.get("/")
async def list_departments(
    college_id: str = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    query = {"college_id": college_id} if college_id else {}
    depts = []
    async for dept in db["departments"].find(query):
        dept = fix_id(dept)
        dept = await enrich(dept, db)
        depts.append(dept)
    return depts


# ── READ ONE  GET /departments/{dept_id} ─────────────────────────────────────

@router.get("/{dept_id}")
async def get_department(
    dept_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    dept = fix_id(await get_or_404(dept_id, db))
    return await enrich(dept, db)


# ── UPDATE (full)  PUT /departments/{dept_id} ─────────────────────────────────

@router.put("/{dept_id}")
async def replace_department(
    dept_id: str,
    dept: DepartmentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Full replacement — all fields required."""
    await get_or_404(dept_id, db)
    await validate_college(dept.college_id, db)
    await db["departments"].update_one({"dept_id": dept_id}, {"$set": dept.dict()})
    return {"message": "Department fully updated"}


# ── UPDATE (partial)  PATCH /departments/{dept_id} ────────────────────────────

@router.patch("/{dept_id}")
async def patch_department(
    dept_id: str,
    dept: DepartmentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Partial update — send only the fields you want to change."""
    await get_or_404(dept_id, db)
    changes = {k: v for k, v in dept.dict().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    if "college_id" in changes:
        await validate_college(changes["college_id"], db)
    await db["departments"].update_one({"dept_id": dept_id}, {"$set": changes})
    return {"message": "Department partially updated", "updated_fields": list(changes.keys())}


# ── DELETE  DELETE /departments/{dept_id} ────────────────────────────────────

@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Blocks deletion if students or employees are still linked."""
    if await db["students"].find_one({"dept_id": dept_id}):
        raise HTTPException(status_code=400, detail="Cannot delete: students are still linked to this department.")
    if await db["employees"].find_one({"dept_id": dept_id}):
        raise HTTPException(status_code=400, detail="Cannot delete: employees are still linked to this department.")
    result = await db["departments"].delete_one({"dept_id": dept_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")