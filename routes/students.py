from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from models import StudentCreate, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


def fix_id(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_or_404(student_id: str, db: AsyncIOMotorDatabase) -> dict:
    doc = await db["students"].find_one({"student_id": student_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
    return doc


async def enrich(student: dict, db: AsyncIOMotorDatabase) -> dict:
    college = await db["colleges"].find_one({"college_id": student.get("college_id")})
    student["college_name"] = college["college_name"] if college else None
    dept = await db["departments"].find_one({"dept_id": student.get("dept_id")})
    student["dept_name"] = dept["dept_name"] if dept else None
    return student


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


# ── CREATE  POST /students ────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await validate_refs(student.college_id, student.dept_id, db)
    if await db["students"].find_one({"student_id": student.student_id}):
        raise HTTPException(status_code=400, detail="Student ID already exists")
    result = await db["students"].insert_one(student.dict())
    return {"message": "Student created", "id": str(result.inserted_id)}


# ── READ ALL  GET /students ───────────────────────────────────────────────────

@router.get("/")
async def list_students(
    college_id: str = None,
    dept_id: str = None,
    year_of_study: int = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    query = {}
    if college_id:
        query["college_id"] = college_id
    if dept_id:
        query["dept_id"] = dept_id
    if year_of_study:
        query["year_of_study"] = year_of_study

    students = []
    async for student in db["students"].find(query):
        student = fix_id(student)
        student = await enrich(student, db)
        students.append(student)
    return students


# ── READ ONE  GET /students/{student_id} ─────────────────────────────────────

@router.get("/{student_id}")
async def get_student(
    student_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    student = fix_id(await get_or_404(student_id, db))
    return await enrich(student, db)


# ── UPDATE (full)  PUT /students/{student_id} ─────────────────────────────────

@router.put("/{student_id}")
async def replace_student(
    student_id: str,
    student: StudentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Full replacement — all fields required."""
    await get_or_404(student_id, db)
    await validate_refs(student.college_id, student.dept_id, db)
    await db["students"].update_one({"student_id": student_id}, {"$set": student.dict()})
    return {"message": "Student fully updated"}


# ── UPDATE (partial)  PATCH /students/{student_id} ────────────────────────────

@router.patch("/{student_id}")
async def patch_student(
    student_id: str,
    student: StudentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Partial update — send only the fields you want to change."""
    await get_or_404(student_id, db)
    changes = {k: v for k, v in student.dict().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    # If either college_id or dept_id is being changed, re-validate both together
    existing = await db["students"].find_one({"student_id": student_id})
    new_college = changes.get("college_id", existing["college_id"])
    new_dept    = changes.get("dept_id",    existing["dept_id"])
    if "college_id" in changes or "dept_id" in changes:
        await validate_refs(new_college, new_dept, db)

    await db["students"].update_one({"student_id": student_id}, {"$set": changes})
    return {"message": "Student partially updated", "updated_fields": list(changes.keys())}


# ── DELETE  DELETE /students/{student_id} ────────────────────────────────────

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    result = await db["students"].delete_one({"student_id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")