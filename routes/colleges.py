from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from models import CollegeCreate, CollegeUpdate

router = APIRouter(prefix="/colleges", tags=["Colleges"])


def fix_id(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_or_404(college_id: str, db: AsyncIOMotorDatabase) -> dict:
    doc = await db["colleges"].find_one({"college_id": college_id})
    if not doc:
        raise HTTPException(status_code=404, detail="College not found")
    return doc


async def attach_departments(college: dict, db: AsyncIOMotorDatabase) -> dict:
    depts = []
    async for dept in db["departments"].find({"college_id": college["college_id"]}):
        depts.append({"dept_id": dept["dept_id"], "dept_name": dept["dept_name"]})
    college["departments"] = depts
    return college


# ── CREATE  POST /colleges ────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_college(
    college: CollegeCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if await db["colleges"].find_one({"college_id": college.college_id}):
        raise HTTPException(status_code=400, detail="College ID already exists")
    result = await db["colleges"].insert_one(college.dict())
    return {"message": "College created", "id": str(result.inserted_id)}


# ── READ ALL  GET /colleges ───────────────────────────────────────────────────

@router.get("/")
async def list_colleges(db: AsyncIOMotorDatabase = Depends(get_database)):
    colleges = []
    async for college in db["colleges"].find():
        college = fix_id(college)
        college = await attach_departments(college, db)
        colleges.append(college)
    return colleges


# ── READ ONE  GET /colleges/{college_id} ─────────────────────────────────────

@router.get("/{college_id}")
async def get_college(
    college_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    college = fix_id(await get_or_404(college_id, db))
    return await attach_departments(college, db)


# ── UPDATE (full)  PUT /colleges/{college_id} ─────────────────────────────────

@router.put("/{college_id}")
async def replace_college(
    college_id: str,
    college: CollegeCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Full replacement — all fields required."""
    await get_or_404(college_id, db)
    await db["colleges"].update_one(
        {"college_id": college_id}, {"$set": college.dict()}
    )
    return {"message": "College fully updated"}


# ── UPDATE (partial)  PATCH /colleges/{college_id} ────────────────────────────

@router.patch("/{college_id}")
async def patch_college(
    college_id: str,
    college: CollegeUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Partial update — send only the fields you want to change."""
    await get_or_404(college_id, db)
    changes = {k: v for k, v in college.dict().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    await db["colleges"].update_one({"college_id": college_id}, {"$set": changes})
    return {"message": "College partially updated", "updated_fields": list(changes.keys())}


# ── DELETE  DELETE /colleges/{college_id} ────────────────────────────────────

@router.delete("/{college_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_college(
    college_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Deletes the college. Blocks deletion if departments are still linked."""
    linked = await db["departments"].find_one({"college_id": college_id})
    if linked:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: departments are still linked to this college. Delete them first.",
        )
    result = await db["colleges"].delete_one({"college_id": college_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="College not found")