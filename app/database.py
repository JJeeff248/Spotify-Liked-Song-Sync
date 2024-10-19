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
        "sync_interval": 24,  # Default sync interval is 24 hours
        "last_sync": None,
        "created_at": datetime.now(timezone.utc)
    }
    return users.insert_one(user)

def get_user(spotify_id):
    return users.find_one({"_id": spotify_id})

def update_user(spotify_id, update_data):
    return users.update_one({"_id": spotify_id}, {"$set": update_data})

def get_all_users():
    return list(users.find())

def get_user_sync_interval(user_id):
    user = users.find_one({"_id": user_id}, {"sync_interval": 1})
    return user.get("sync_interval", 24) if user else 24  # Default to 24 hours if not set
