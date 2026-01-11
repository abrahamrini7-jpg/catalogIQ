import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_db():
    # Uses the connection string from your Atlas 'Connect' button
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client.photo_workflow  # This must match your DB name in Compass