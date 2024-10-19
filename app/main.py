from flask import Flask, render_template, redirect, request, session, jsonify, Response
from auth import get_auth_url, get_token, refresh_token, get_user_playlists
from sync import sync_liked_songs, get_playlist_info, find_matching_playlist, create_playlist
import os
from dotenv import load_dotenv
import json
import time
from database import create_user, get_user, update_user, get_all_users, get_user_sync_interval
import requests
import threading
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

def background_sync():
    with app.app_context():
        while True:
            users = get_all_users()
            current_time = datetime.now(timezone.utc)
            
            for user in users:
                if user["is_syncing"] and user["playlist_id"] and user["sync_interval"]:
                    last_sync = user["last_sync"]
                    if last_sync:
                        last_sync = last_sync.replace(tzinfo=timezone.utc)
                    else:
                        last_sync = datetime.min.replace(tzinfo=timezone.utc)
                    
                    time_since_last_sync = (current_time - last_sync).total_seconds() / 60  # in minutes
                    
                    if time_since_last_sync >= user["sync_interval"]:
                        try:
                            new_token_info = refresh_token(user["refresh_token"])
                            access_token = new_token_info["access_token"]
                            
                            update_user(user["_id"], {"access_token": access_token})
                            
                            sync_liked_songs(access_token, user["playlist_id"], user["sync_interval"])
                            
                            update_user(user["_id"], {"last_sync": datetime.now(timezone.utc)})
                        except Exception as e:
                            print(f"Error syncing for user {user['_id']}: {str(e)}")
            
            time.sleep(60)

sync_thread = threading.Thread(target=background_sync, daemon=True)
sync_thread.start()

@app.route("/")
def index():
    if "access_token" not in session:
        return render_template("index.html")
    return redirect("/settings")

@app.route("/login")
def login():
    return redirect(get_auth_url())

@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"Error during Spotify authentication: {error}", 400

    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    try:
        token_info = get_token(code)
        if "error" in token_info:
            return f"Error getting access token: {token_info['error']}", 400

        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        user_profile = requests.get("https://api.spotify.com/v1/me", headers=headers).json()
        spotify_id = user_profile["id"]

        user = get_user(spotify_id)
        if not user:
            create_user(spotify_id, access_token, refresh_token)
        else:
            update_user(spotify_id, {"access_token": access_token, "refresh_token": refresh_token})

        session["spotify_id"] = spotify_id
        return redirect("/settings")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route("/settings", methods=["GET"])
def settings():
    if "spotify_id" not in session:
        return redirect("/")
    
    user = get_user(session["spotify_id"])
    if not user:
        return redirect("/logout")

    playlists = get_user_playlists(user["access_token"])
    
    current_playlist = None
    matching_playlist_id = None

    if user["playlist_id"]:
        current_playlist = get_playlist_info(user["access_token"], user["playlist_id"])
    else:
        matching_playlist_id = find_matching_playlist(user["access_token"], playlists)
        if matching_playlist_id:
            current_playlist = get_playlist_info(user["access_token"], matching_playlist_id)
            update_user(session["spotify_id"], {"playlist_id": matching_playlist_id})
    
    user_id = user["_id"]
    user_sync_interval = get_user_sync_interval(user_id)

    return render_template("settings.html", 
                           playlists=playlists, 
                           current_playlist=current_playlist, 
                           matching_playlist_id=matching_playlist_id,
                           is_syncing=user["is_syncing"],
                           user_sync_interval=user_sync_interval)

@app.route("/toggle_sync", methods=["POST"])
def toggle_sync():
    if "spotify_id" not in session:
        return redirect("/")
    
    user = get_user(session["spotify_id"])
    if not user:
        return redirect("/logout")

    if user["is_syncing"]:
        update_user(session["spotify_id"], {"is_syncing": False})
    else:
        playlist_id = request.form.get("playlist_id")
        sync_interval = int(request.form.get("sync_interval"))
        update_user(session["spotify_id"], {
            "playlist_id": playlist_id,
            "sync_interval": sync_interval,
            "is_syncing": True
        })
        sync_liked_songs(user["access_token"], playlist_id, sync_interval)
    
    return redirect("/settings")

@app.route("/sync")
def sync():
    if "access_token" not in session:
        return redirect("/")
    
    playlist_id = session.get("playlist_id")
    sync_interval = session.get("sync_interval")
    
    sync_liked_songs(session["access_token"], playlist_id, sync_interval)
    
    return "Sync started successfully!"

@app.route("/stop_sync")
def stop_sync():
    session.pop("playlist_id", None)
    session.pop("sync_interval", None)
    return redirect("/settings")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route('/sync-progress')
def sync_progress():
    def generate():
        while True:
            progress = getattr(app, 'sync_progress', None)
            if progress:
                yield f"data: {json.dumps(progress)}\n\n"
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route("/create_playlist", methods=["POST"])
def create_new_playlist():
    if "access_token" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json
    playlist_name = data.get("name")
    
    if not playlist_name:
        return jsonify({"error": "Playlist name is required"}), 400
    
    new_playlist = create_playlist(session["access_token"], playlist_name)
    
    if new_playlist:
        return jsonify(new_playlist)
    else:
        return jsonify({"error": "Failed to create playlist"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
