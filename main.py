import dotenv as env
import requests
import os
import base64
import json
import webbrowser

env.load_dotenv()

id = os.getenv("CLIENT_ID")
secret = os.getenv('CLIENT_SEC')
scope = 'user-top-read'
redirect_URI = 'https://localhost:3000/callback'
code = 'AQD1uO33DLWH9_w0VFBN3Y268Es8uFjSZ6yTKObOTpOY0gOLqJabZ0FBDRr8Be51tlvNx56rKEeAtwy-QMmF179cFjIIvn45oyvxWTzc63g7XmD8rmc5cViNJ2xAk9VQiBWjvgcqyRwgpJsMw41QOlCPLoGx_p_Od4JSqARx3fAUy6QmVrdjqcNQfD0HRhJYj4E'


def authorization():
    url = "https://accounts.spotify.com/authorize?"
    
    query = {
        'response_type': 'code',
        'client_id': id,
        'scope': scope,
        'redirect_uri': redirect_URI
    }

    auth_url = url + '&'.join([f"{key}={value}" for key,value in query.items()])
    webbrowser.open(auth_url)
    
    

def get_token():
    auth = id + ":" + secret
    auth_byte = auth.encode("utf-8")
    
    auth_base64 = str(base64.b64encode(auth_byte),"utf-8")

    url = "https://accounts.spotify.com/api/token"
    header = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = data = {
        "grant_type": "authorization_code",
        "code":code,
        "redirect_uri": redirect_URI
    }
    result = requests.post(url,headers=header,data=data)
    
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {
        "Authorization":"Bearer " + token
        }


def get_artist(token,artist_name):

    url = 'https://api.spotify.com/v1/search'
    header = get_auth_header(token)

    query = f'?q={artist_name}&type=artist&limit=1'
    query_url = url + query

    result = requests.get(query_url,headers=header)
    json_result = json.loads(result.content)
    return json_result['artists']['items']



def get_artist_songs(token,artist_name):

    offset = 0
    url = f'https://api.spotify.com/v1/search?type=track&limit=50&offset={offset}&q=artist:{artist_name}'
    tracks = []
    header = get_auth_header(token)

    while offset <= 300:
        result = requests.get(url,headers=header)
        json_result = json.loads(result.content)
        for items in json_result['tracks']['items']:
            print(items['name'])
        
        offset += 50
        url = f'https://api.spotify.com/v1/search?type=track&limit=50&offset={offset}&q=artist:{artist_name}'

def get_user_tracks(token):
    url = 'https://api.spotify.com/v1/me/top/tracks'
    header = get_auth_header(token)
    result = requests.get(url,headers=header)
    json_result = json.loads(result.content)
    print(json_result)


#authorization()
user_token = get_token()

get_user_tracks(user_token)
#artist_songs = get_artist_songs(user_token,'Kanye')
