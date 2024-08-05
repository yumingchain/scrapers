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

def search_for_show(token, show_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={show_name}&type=show&limit=1"

    query_url = url + query
    query_url = "https://api.spotify.com/v1/search?q={The Joe Rogan Experience}&type=show&limit=1"
    response = get(query_url, headers=headers)
    json_response = json.loads(response.content)["shows"]

    if len(json_response) == 0:
        print("No show found")
        return None
    
    return json_response

def get_show_info(token, show_id):
    url = f"https://api.spotify.com/v1/shows/{show_id}"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    json_response = json.loads(response.content)

    return json_response

token = get_token()
result = get_show_info(token, "4rOoJ6Egrf8K2IrywzwOMk")
result = search_for_show(token, "The Joe Rogan Experience")
# show_id = result["id"]
print(result)
# songs = get_songs_by_show(token, show_id)

# for idx, song in enumerate (songs):
#     print(f"{idx + 1} . {song['name']}")
