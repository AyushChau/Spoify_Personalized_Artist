from flask import Flask, redirect, request, jsonify, session, render_template
import requests
import urllib.parse
import os
import dotenv as env
import datetime
import base64
import json
import sqlite3
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio

id = os.getenv("CLIENT_ID")
secret = os.getenv('CLIENT_SEC')
redirect_URI = 'http://localhost:3000/callback'
auth_URL = 'https://accounts.spotify.com/authorize'
token_URL = 'https://accounts.spotify.com/api/token'
base_URL = 'https://api.spotify.com/v1/'
sql_connection = sqlite3.connect('spotify_data.db', check_same_thread=False)
cur = sql_connection.cursor()
user_data = ''
artist_data = ''

app = Flask(__name__)
app.secret_key = '53d344f9-543a-6039-a123-1f9579440851'


def get_auth_header(token):
    return {
        "Authorization":"Bearer " + token
        }

def tablecreation():
    cur.execute("DROP TABLE IF EXISTS user_tracks")
    cur.execute("DROP TABLE IF EXISTS artist_tracks")
    cur.execute("CREATE TABLE user_tracks(id VARCHAR(100),song_name VARCHAR(50), acousticness FLOAT,danceability FLOAT,energy FLOAT,instrumentalness FLOAT,liveness FLOAT,loudness FLOAT,mode INTEGER,speechiness FLOAT,tempo FLOAT,valence FLOAT)")
    cur.execute("CREATE TABLE artist_tracks(id VARCHAR(100),song_name VARCHAR(50), image VARCHAR(200), acousticness FLOAT,danceability FLOAT,energy FLOAT,instrumentalness FLOAT,liveness FLOAT,loudness FLOAT,mode INTEGER,speechiness FLOAT,tempo FLOAT,valence FLOAT)")


async def fetch_tracks(time_range,header):
    all_tracks = []
    next_url = base_URL + f'me/top/tracks?limit=50&time_range={time_range}'

    async with aiohttp.ClientSession() as session:
        while next_url:
            async with session.get(next_url,headers=header) as response:
                tracks = await response.json()
                for track in tracks['items']:
                    all_tracks.append(track['id'])
        
                next_url = tracks['next']

    
    return all_tracks


async def get_user_track_ids():

    header = get_auth_header(session['access_token'])
    time_ranges = ['medium_term'] #Figure out how to make this shit faster!!!
    all_tracks = []
    tasks = []

    for ranges in time_ranges:
        tasks.append(fetch_tracks(ranges,header))

    for task in asyncio.as_completed(tasks):
        all_tracks.extend(await task)

    return list(set(all_tracks))


def populate_dataframe(ids,context):
    global user_data, artist_data

    inserter = []
    id_chunks = [ids[i:i+50] for i in range(0, len(ids), 50)]
    header = get_auth_header(session['access_token'])

    for i in range(len(id_chunks)):
        ids_str = ','.join(str(id) for id in id_chunks[0])
        json_feature_result = requests.get(base_URL + f'audio-features?ids={ids_str}',headers=header)
        json_song_result = requests.get(base_URL + f'tracks?ids={ids_str}',headers=header)

        result_feature = json.loads(json_feature_result.content)
        result_song = json.loads(json_song_result.content)


    
    if context == 'user':
        for j in range(len(id_chunks[i])):
            inserter.append([id_chunks[i][j],result_song['tracks'][j]['name'],result_feature['audio_features'][j]['acousticness'],result_feature['audio_features'][j]['danceability'],result_feature['audio_features'][j]['energy'],result_feature['audio_features'][j]['instrumentalness'],result_feature['audio_features'][j]['liveness'],result_feature['audio_features'][j]['loudness'],result_feature['audio_features'][j]['mode'],result_feature['audio_features'][j]['speechiness'],result_feature['audio_features'][j]['tempo'],result_feature['audio_features'][j]['valence']])
        cur.executemany('INSERT INTO user_tracks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',inserter)
        user_data = pd.read_sql_query("SELECT * from user_tracks",sql_connection)
    elif context == 'artist':
        cur.execute('DELETE FROM artist_tracks')
        for j in range(len(id_chunks[i])):
            inserter.append([id_chunks[i][j],result_song['tracks'][j]['name'],result_song['tracks'][j]['album']['images'][0]['url'],result_feature['audio_features'][j]['acousticness'],result_feature['audio_features'][j]['danceability'],result_feature['audio_features'][j]['energy'],result_feature['audio_features'][j]['instrumentalness'],result_feature['audio_features'][j]['liveness'],result_feature['audio_features'][j]['loudness'],result_feature['audio_features'][j]['mode'],result_feature['audio_features'][j]['speechiness'],result_feature['audio_features'][j]['tempo'],result_feature['audio_features'][j]['valence']])
        cur.executemany('INSERT INTO artist_tracks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',inserter)
        artist_data = pd.read_sql_query("SELECT * from artist_tracks",sql_connection)

def artist_songs(artist_name):

    offset = 0

    url = base_URL + f'search?type=track&limit=50&offset={offset}&q=artist:{artist_name}'
    tracks = []
    header = get_auth_header(session['access_token'])

    while offset <= 40:
        result = requests.get(url,headers=header)
        json_result = json.loads(result.content)
        for items in json_result['tracks']['items']:
            tracks.append(items['id'])
        
        offset += 50
        url = base_URL + f'search?type=track&limit=50&offset={offset}&q=artist:{artist_name}'

    return tracks


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    scope = 'user-top-read'

    params = {
        'client_id': id,
        'response_type':'code',
        'scope': scope,
        'redirect_uri': redirect_URI,
        'show_dialog': True
    }

    auth = f'{auth_URL}?{urllib.parse.urlencode(params)}'

    return redirect(auth)


@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({'error':request.args['error']})
    
    if 'code' in request.args:

        auth = id + ":" + secret
        auth_byte = auth.encode("utf-8")
    
        auth_base64 = str(base64.b64encode(auth_byte),"utf-8")

        header = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            'grant_type': 'authorization_code',
            'code': request.args['code'],
            'redirect_uri': redirect_URI
        }

        response = requests.post(token_URL,headers=header,data=data)

        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.datetime.now().timestamp() + token_info['expires_in']

        return redirect('/user_tracks')


@app.route('/user_tracks')
async def get_user_tracks():

    if 'access_token' not in session:
        return redirect('/login')

    else:
        #track_ids = await get_user_track_ids()
        #populate_dataframe(track_ids,'user')
        return render_template('search_page.html')
    


@app.route('/artist_songs')
def get_artist_songs():

    if 'access_token' not in session:
        return redirect('/login')

    else:
        song_ids = artist_songs(request.args.get('artist_name'))
        populate_dataframe(song_ids,'artist')
        
        artist_data['Temp'] = 20

        return render_template('artist.html',table=artist_data[['song_name','image','Temp']].to_dict(orient='records'))


@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    else:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': id,
            'client_secret': secret
        }

        response = requests.post(token_URL,data=req_body) 

        new_token = response.json()

        session['acess_token'] = new_token['access_token']
        session['expires_at'] = datetime.datetime.now().timestamp() + new_token['expires_in']

        return redirect('/user_tracks')

if __name__ == '__main__':
    env.load_dotenv()

    tablecreation()
    app.run(port=3000,debug=True)
