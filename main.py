from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import database
from routes import colleges, departments, students, employees


# ── Lifespan (replaces deprecated on_event) ───────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open MongoDB connection and create indexes
    database.client = AsyncIOMotorClient(database.MONGO_URI)
    db = database.get_database()

    # Unique indexes to enforce ID uniqueness
    await db["colleges"].create_index("college_id", unique=True)
    await db["departments"].create_index("dept_id", unique=True)
    await db["students"].create_index("student_id", unique=True)
    await db["employees"].create_index("employee_id", unique=True)

    # Lookup indexes for faster joins
    await db["departments"].create_index("college_id")
    await db["students"].create_index("college_id")
    await db["students"].create_index("dept_id")
    await db["employees"].create_index("college_id")
    await db["employees"].create_index("dept_id")

    print("✅ Connected to MongoDB and indexes created.")
    yield

    # Shutdown: close connection
    database.client.close()
    print("🔌 MongoDB connection closed.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="College Management API",
    description="Manage colleges, departments, students and employees with full referential integrity.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(colleges.router)
app.include_router(departments.router)
app.include_router(students.router)
app.include_router(employees.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "College Management API is running"}