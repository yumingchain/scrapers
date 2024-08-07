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

def search_for_show(token, show_name, market="US", limit=100):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    shows = []
    
    for offset in range(0, limit, 50):
        query = f"?q={show_name}&type=show&limit=50&offset={offset}&market={market}"
        query_url = url + query
        response = get(query_url, headers=headers)

        print(f"Response Status Code: {response.status_code}")

        json_response = json.loads(response.content)

        if "shows" in json_response and "items" in json_response["shows"]:
            shows.extend(json_response["shows"]["items"])
        
        if len(json_response["shows"]["items"]) < 50:
            break  # No more shows to fetch
    
    return shows

def get_episodes_by_show(token, show_id, limit=100):
    url = f"https://api.spotify.com/v1/shows/{show_id}/episodes"
    headers = get_auth_header(token)
    episodes = []
    
    for offset in range(0, limit, 50):
        query = f"?limit=50&offset={offset}"
        query_url = url + query
        response = get(query_url, headers=headers)
        
        json_response = json.loads(response.content)
        
        if "items" in json_response:
            episodes.extend(json_response["items"])
        
        if len(json_response["items"]) < 50:
            break  # No more episodes to fetch
    
    return episodes

token = get_token()
results = search_for_show(token, "podcast", market="US", limit=300)

if results:
    for idx, show in enumerate(results):
        show_name = show['name']
        show_name = show_name.encode('ascii', 'replace').decode('ascii')  # Replace non-ASCII characters
        print(f"{idx + 1}. {show_name} (ID: {show['id']})")

        show_id = show["id"]

        episodes = get_episodes_by_show(token, show_id, limit=100)
        for episode_idx, episode in enumerate(episodes):
            episode_name = episode['name']
            episode_name = episode_name.encode('ascii', 'replace').decode('ascii')
            print(f"  {episode_idx + 1}. {episode_name} (ID: {episode['id']})")
else:
    print("No shows found")
