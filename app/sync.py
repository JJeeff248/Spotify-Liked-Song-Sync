import requests
from flask import current_app
from typing import List, Set, Dict, Optional

def get_liked_songs(access_token: str) -> List[Dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/tracks"
    liked_songs = []

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        liked_songs.extend(data["items"])
        url = data.get("next")

    return liked_songs

def get_or_create_playlist(access_token: str, playlist_name: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}

    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    user_id = user_response.json()["id"]

    playlists_response = requests.get(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers)
    playlists = playlists_response.json()["items"]

    for playlist in playlists:
        if playlist["name"] == playlist_name:
            return playlist["id"]

    create_response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        json={"name": playlist_name, "public": False}
    )
    return create_response.json()["id"]

def get_playlist_info(access_token: str, playlist_id: str) -> Dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}", headers=headers)
    return response.json()

def get_playlist_tracks(access_token: str, playlist_id: str) -> Set[str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    playlist_tracks = set()

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        playlist_tracks.update(item['track']['id'] for item in data['items'])
        url = data.get('next')

    return playlist_tracks

def sync_liked_songs(access_token: str, playlist_id: str, sync_interval: int) -> int:
    with current_app.app_context():
        headers = {"Authorization": f"Bearer {access_token}"}

        existing_tracks = get_playlist_tracks(access_token, playlist_id)
        liked_songs = get_liked_songs(access_token)

        new_songs = [song for song in liked_songs if song['track']['id'] not in existing_tracks]
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

            progress = min((i + 100) / len(track_uris) * 100, 100) if track_uris else 100
            current_app.sync_progress = {
                'current': added_songs,
                'total': len(new_songs),
                'percentage': progress
            }

        print(f"Added {added_songs} new songs to playlist")
        return added_songs

def compare_playlists(access_token: str, liked_track_ids: Set[str], playlist_id: str) -> float:
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
    match_percentage = len(common_tracks) / len(liked_track_ids) * 100 if liked_track_ids else 0

    return match_percentage

def find_matching_playlist(access_token: str, playlists: List[Dict]) -> Optional[str]:
    liked_songs = get_liked_songs(access_token)
    liked_track_ids = set(song['track']['id'] for song in liked_songs)
    best_match = None
    highest_percentage = 0

    for playlist in playlists:
        match_percentage = compare_playlists(access_token, liked_track_ids, playlist['id'])
        if match_percentage > highest_percentage:
            highest_percentage = match_percentage
            best_match = playlist['id']

        if match_percentage >= 75:
            return playlist['id']

    return best_match

def create_playlist(access_token: str, name: str) -> Optional[Dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    user_profile = requests.get("https://api.spotify.com/v1/me", headers=headers).json()
    user_id = user_profile["id"]

    data = {
        "name": name,
        "public": False,
        "description": "Created by Spotify Sync"
    }

    response = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers, json=data)

    if response.status_code == 201:
        return response.json()
    else:
        return None
