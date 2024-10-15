from flask import Flask, render_template, redirect, request, session, jsonify, Response
from auth import get_auth_url, get_token, refresh_token, get_user_playlists
from sync import sync_liked_songs, get_playlist_info, find_matching_playlist, create_playlist
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

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

        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        return redirect("/settings")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route("/settings", methods=["GET"])
def settings():
    if "access_token" not in session:
        return redirect("/")
    
    playlists = get_user_playlists(session["access_token"])
    
    # Find matching playlist
    matching_playlist_id = find_matching_playlist(session["access_token"], playlists)
    
    current_playlist = None
    if "playlist_id" in session:
        current_playlist = get_playlist_info(session["access_token"], session["playlist_id"])
    elif matching_playlist_id:
        current_playlist = get_playlist_info(session["access_token"], matching_playlist_id)
        session["playlist_id"] = matching_playlist_id
    
    is_syncing = "is_syncing" in session and session["is_syncing"]
    
    return render_template("settings.html", 
                           playlists=playlists, 
                           current_playlist=current_playlist, 
                           matching_playlist_id=matching_playlist_id,
                           is_syncing=is_syncing)

@app.route("/toggle_sync", methods=["POST"])
def toggle_sync():
    if "access_token" not in session:
        return redirect("/")
    
    if "is_syncing" in session and session["is_syncing"]:
        # Stop syncing
        session["is_syncing"] = False
        # Here you would typically stop your background sync process
    else:
        # Start syncing
        playlist_id = request.form.get("playlist_id")
        sync_interval = int(request.form.get("sync_interval"))
        session["playlist_id"] = playlist_id
        session["sync_interval"] = sync_interval
        session["is_syncing"] = True
        # Here you would typically start your background sync process
        sync_liked_songs(session["access_token"], playlist_id, sync_interval)
    
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
