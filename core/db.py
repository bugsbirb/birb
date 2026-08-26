import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL not set")

client = AsyncMongoClient(
    MONGO_URL,
    maxIdleTimeMS=60000,
    minPoolSize=0,
)

db = (
    client["BETA"]
    if ENVIRONMENT and ENVIRONMENT.lower() == "development"
    else client["astro"]
)
