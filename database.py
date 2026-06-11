from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "college_db")

client: AsyncIOMotorClient = None


def get_database() -> AsyncIOMotorDatabase:
    return client[DB_NAME]