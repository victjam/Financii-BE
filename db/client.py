from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path

env_file = ".env"
if os.getenv("ENVIRONMENT") == "production":
    env_file = ".env.prod"

env_path = Path(".") / env_file
load_dotenv(dotenv_path=env_path)

database_uri = os.getenv("DATABASE_URL")

db_client = MongoClient(database_uri).financii_db
