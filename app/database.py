from pymongo import MongoClient
import os
from datetime import datetime, timezone

client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_default_database()
users = db.users

def create_user(spotify_id, access_token, refresh_token):
    user = {
        "_id": spotify_id,  # Use spotify_id as the primary key
        "access_token": access_token,
        "refresh_token": refresh_token,
        "playlist_id": None,
        "is_syncing": False,
        "sync_interval": None,
        "last_sync": None,
        "created_at": datetime.now(timezone.utc)
    }
    return users.insert_one(user)

def get_user(spotify_id):
    return users.find_one({"_id": spotify_id})

def update_user(spotify_id, update_data):
    return users.update_one({"_id": spotify_id}, {"$set": update_data})
