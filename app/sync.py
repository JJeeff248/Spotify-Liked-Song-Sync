import requests
import time
from auth import refresh_token
from flask import current_app


def get_liked_songs(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/tracks"
    liked_songs = []

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        liked_songs.extend(data["items"])
        url = data.get("next")

    return liked_songs


def get_or_create_playlist(access_token, playlist_name):
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get user ID
    user_response = requests.get(
        "https://api.spotify.com/v1/me", headers=headers)
    user_id = user_response.json()["id"]

    # Check if playlist exists
    playlists_response = requests.get(
        f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers)
    playlists = playlists_response.json()["items"]

    for playlist in playlists:
        if playlist["name"] == playlist_name:
            return playlist["id"]

    # Create new playlist if it doesn't exist
    create_response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        json={"name": playlist_name, "public": False}
    )
    return create_response.json()["id"]


def get_playlist_info(access_token, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}", headers=headers)
    return response.json()


def get_playlist_tracks(access_token, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    playlist_tracks = set()

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        playlist_tracks.update(item['track']['id'] for item in data['items'])
        url = data.get('next')

    return playlist_tracks


def sync_liked_songs(access_token, playlist_id, sync_interval):
    with current_app.app_context():
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get existing tracks in the playlist
        existing_tracks = get_playlist_tracks(access_token, playlist_id)

        # Get liked songs
        liked_songs = get_liked_songs(access_token)
        total_songs = len(liked_songs)

        # Filter out songs that are already in the playlist
        new_songs = [song for song in liked_songs if song['track']
                     ['id'] not in existing_tracks]

        track_uris = [song["track"]["uri"] for song in new_songs]

        added_songs = 0
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i+100]
            response = requests.post(
                f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                headers=headers,
                json={"uris": chunk}
            )
            if response.status_code == 201:
                added_songs += len(chunk)

            progress = min((i + 100) / len(track_uris) *
                           100, 100) if track_uris else 100
            current_app.sync_progress = {
                'current': added_songs,
                'total': len(new_songs),
                'percentage': progress
            }

        print(f"Added {added_songs} new songs to playlist")
        return added_songs


def compare_playlists(access_token, liked_track_ids, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    playlist_tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        playlist_tracks.extend([item['track']['id'] for item in data['items']])
        url = data.get('next')

    playlist_track_ids = set(playlist_tracks)

    common_tracks = liked_track_ids.intersection(playlist_track_ids)
    match_percentage = len(common_tracks) / \
        len(liked_track_ids) * 100 if liked_track_ids else 0

    return match_percentage


def find_matching_playlist(access_token, playlists):
    liked_songs = get_liked_songs(access_token)
    liked_track_ids = set(song['track']['id'] for song in liked_songs)
    best_match = None
    highest_percentage = 0

    for playlist in playlists:
        match_percentage = compare_playlists(
            access_token, liked_track_ids, playlist['id'])
        if match_percentage > highest_percentage:
            highest_percentage = match_percentage
            best_match = playlist['id']

        if match_percentage >= 75:
            return playlist['id']

    return best_match


def create_playlist(access_token, name):
    headers = {"Authorization": f"Bearer {access_token}"}
    user_profile = requests.get(
        "https://api.spotify.com/v1/me", headers=headers).json()
    user_id = user_profile["id"]

    data = {
        "name": name,
        "public": False,
        "description": "Created by Spotify Sync"
    }

    response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers, json=data)

    if response.status_code == 201:
        return response.json()
    else:
        return None
