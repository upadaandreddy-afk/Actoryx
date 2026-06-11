"""
Run this once to seed sample data:
    python seed.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "college_db")


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # Clear existing data
    for col in ["colleges", "departments", "students", "employees"]:
        await db[col].drop()

    # ── Colleges ──────────────────────────────────────────────────────────────
    colleges = [
        {"college_id": "CLG001", "college_name": "MIT College of Engineering", "location": "Hyderabad", "established_year": 1990},
        {"college_id": "CLG002", "college_name": "JNTU College of Technology", "location": "Warangal",  "established_year": 1975},
    ]
    await db["colleges"].insert_many(colleges)
    print(f"Inserted {len(colleges)} colleges")

    # ── Departments ───────────────────────────────────────────────────────────
    departments = [
        {"dept_id": "CSE001", "dept_name": "Computer Science",       "college_id": "CLG001"},
        {"dept_id": "ECE001", "dept_name": "Electronics & Comm.",     "college_id": "CLG001"},
        {"dept_id": "MECH01", "dept_name": "Mechanical Engineering",  "college_id": "CLG001"},
        {"dept_id": "CSE002", "dept_name": "Computer Science",        "college_id": "CLG002"},
        {"dept_id": "CIVIL2", "dept_name": "Civil Engineering",       "college_id": "CLG002"},
    ]
    await db["departments"].insert_many(departments)
    print(f"Inserted {len(departments)} departments")

    # ── Students ──────────────────────────────────────────────────────────────
    students = [
        {"student_id": "STU2024001", "student_name": "Ravi Kumar",    "email": "ravi@mit.edu",    "phone": "9876543210", "age": 20, "year_of_study": 2, "dept_id": "CSE001", "college_id": "CLG001"},
        {"student_id": "STU2024002", "student_name": "Priya Singh",   "email": "priya@mit.edu",   "phone": "9876543211", "age": 21, "year_of_study": 3, "dept_id": "ECE001", "college_id": "CLG001"},
        {"student_id": "STU2024003", "student_name": "Arjun Reddy",   "email": "arjun@jntu.edu",  "phone": "9876543212", "age": 19, "year_of_study": 1, "dept_id": "CSE002", "college_id": "CLG002"},
        {"student_id": "STU2024004", "student_name": "Sneha Patel",   "email": "sneha@jntu.edu",  "phone": "9876543213", "age": 22, "year_of_study": 4, "dept_id": "CIVIL2", "college_id": "CLG002"},
    ]
    await db["students"].insert_many(students)
    print(f"Inserted {len(students)} students")

    # ── Employees ─────────────────────────────────────────────────────────────
    employees = [
        {"employee_id": "EMP001", "employee_name": "Dr. Anand Rao",     "email": "anand@mit.edu",   "phone": "9123456781", "designation": "Professor",        "salary": 95000.0, "dept_id": "CSE001", "college_id": "CLG001"},
        {"employee_id": "EMP002", "employee_name": "Dr. Lakshmi Devi",  "email": "lakshmi@mit.edu", "phone": "9123456782", "designation": "Associate Professor","salary": 80000.0, "dept_id": "ECE001", "college_id": "CLG001"},
        {"employee_id": "EMP003", "employee_name": "Prof. Suresh Babu", "email": "suresh@jntu.edu", "phone": "9123456783", "designation": "Professor",        "salary": 90000.0, "dept_id": "CSE002", "college_id": "CLG002"},
        {"employee_id": "EMP004", "employee_name": "Dr. Meena Kumari",  "email": "meena@jntu.edu",  "phone": "9123456784", "designation": "Assistant Professor","salary": 70000.0, "dept_id": "CIVIL2", "college_id": "CLG002"},
    ]
    await db["employees"].insert_many(employees)
    print(f"Inserted {len(employees)} employees")

    client.close()
    print("\n✅ Seed complete! Run: uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(seed())