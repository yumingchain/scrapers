from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth_string = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(encoded_auth_string), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "authorization": f"Basic {auth_base64}",
        "content-type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}

    response = post(url, headers=headers, data=data)
    json_response = json.loads(response.content)
    token = json_response["access_token"]

    return token

def get_auth_header(token):
    return {"authorization": f"Bearer {token}"}

def search_for_show(token, show_name, market="US"):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    shows = []
    offset = 0
    limit = 50  # Spotify's maximum limit per request
    
    while True:
        query = f"?q={show_name}&type=show&market={market}&limit={limit}&offset={offset}"
        query_url = url + query
        response = get(query_url, headers=headers)
        json_response = json.loads(response.content)

        if "shows" in json_response and "items" in json_response["shows"]:
            shows.extend(json_response["shows"]["items"])
        else:
            break
        
        if len(json_response["shows"]["items"]) < limit:
            break
        
        offset += limit  # Move to the next batch

    return shows if shows else None

def get_all_episodes(token, show_id):
    url = f"https://api.spotify.com/v1/shows/{show_id}/episodes"
    headers = get_auth_header(token)
    episodes = []
    offset = 0
    limit = 50
    
    while True:
        query_url = f"{url}?limit={limit}&offset={offset}"
        response = get(query_url, headers=headers)
        json_response = json.loads(response.content)

        if "items" in json_response:
            episodes.extend(json_response["items"])
        else:
            break
        
        if len(json_response["items"]) < limit:
            break
        
        offset += limit  # Move to the next batch
    
    return episodes

token = get_token()
results = search_for_show(token, "The Joe Rogan Experience")

if results:
    for idx, show in enumerate(results):
        show_name = show['name']
        show_name = show_name.encode('ascii', 'replace').decode('ascii')  # Replace non-ASCII characters
        show_id = show['id']
        number_of_episodes = show['total_episodes']
        host = show['publisher']
        print(f"{idx + 1}. {show_name} (ID: {show_id})")

        episodes = get_all_episodes(token, show_id)
        for episode_idx, episode in enumerate(episodes):
            if episode is None:
                print(f"  {episode_idx + 1}. Episode is None (Skipping)")
                continue  # Skip to the next episode if this one is None

            episode_name = episode.get('name', 'Unknown Title')  # Use get() to safely access the key
            episode_name = episode_name.encode('ascii', 'replace').decode('ascii')
            episode_id = episode.get('id', 'Unknown ID')
            episode_duration = episode.get('duration_ms', 0)
            episode_description = episode.get('description', 'No description available')
            episode_date = episode.get('release_date', 'Unknown date')

            print(f"  {episode_idx + 1}. {episode_name} (ID: {episode_id})")

            episode_dict = {
                "podcast_name": show_name,
                "podcast_id": show_id,
                "number_of_episodes": number_of_episodes,
                "episode_name": episode_name,
                "episode_id": episode_id,
                "episode_number": episode_idx + 1,
                "episode_duration": episode_duration,
                "host": host,
                "episode_date": episode_date,
                "episode_description": episode_description,
                "youtube_url": "",
                "apple_url": "",
                "spotify_url": "",
            }

            print(json.dumps(episode_dict, ensure_ascii=True))

else:
    print("No shows found")
