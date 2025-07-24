import sqlite3
import contextlib
import pathlib
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# === SQLite setup ===
DB_PATH = pathlib.Path("storage/index.db")
DB_PATH.parent.mkdir(exist_ok=True)

@contextlib.contextmanager
def get_conn():
    # Create the SQLite database and tables if they do not exist
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_repos(
            repo_url TEXT PRIMARY KEY,
            job_id   TEXT,
            finished_at TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_videos(
            video_url      TEXT PRIMARY KEY,
            audio_path     TEXT,
            transcript_path TEXT,
            created_at     TEXT
        );
        """
    )
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

# === MongoDB setup ===
load_dotenv()  
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

# Test MongoDB connection
try:
    client.admin.command('ping')
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print("❌ Error connecting to MongoDB:", e)

# Define the database and collections
mongo_db = client["crawler_data"]
youtube_collection = mongo_db["youtube_data"]
github_collection = mongo_db["github_data"]
