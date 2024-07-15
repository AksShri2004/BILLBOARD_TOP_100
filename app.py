from flask import Flask, request, render_template
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        travel_time = request.form['travel_time']
        songs = scrape_billboard(travel_time)
        playlist = create_spotify_playlist(travel_time, songs)
        embed_url = get_embed_url(playlist)
        return render_template('result.html', embed_url=embed_url)
    return render_template('index.html')

def scrape_billboard(travel_time):
    response = requests.get(f"https://www.billboard.com/charts/hot-100/{travel_time}")
    soup = BeautifulSoup(response.text, "lxml")
    song_title = soup.find_all(name="h3", id="title-of-a-story")
    songs = []
    for article in song_title:
        if not "Songwriter(s)" in article.getText() and not "Producer(s):" in article.getText() and not "Imprint/Promotion Label:" in article.getText():
            art = article.getText().strip("\n\t")
            songs.append(art)
    return songs

def create_spotify_playlist(travel_time, songs):
    APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=APP_CLIENT_ID,
                                                               client_secret=CLIENT_SECRET))
    playlist = []
    for n in songs:
        try:
            get_req = sp.search(q=f"{n}", limit=1, offset=0, type='track', market=None)
            track = get_req["tracks"]['items'][0]["uri"]
            playlist.append(track)
        except:
            pass
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=APP_CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri="http://example.com/callback", state=None,
                                                   scope="playlist-modify-private", cache_path=None, username=None,
                                                   proxies=None, show_dialog=False, requests_session=True,
                                                   requests_timeout=None))
    USER = os.getenv("USER")
    pl = sp.user_playlist_create(user=USER, name=f"Billboard Top 100 {travel_time}", public=False,
                                 collaborative=False, description='')
    while len(playlist) != 0:
        pl_1 = sp.playlist_add_items(playlist_id=pl["id"], items=[playlist[0]])
        playlist.pop(0)
    return pl["id"]

def get_embed_url(playlist_id):
    return f"https://open.spotify.com/embed/playlist/{playlist_id}"

if __name__ == '__main__':
    app.run(debug=True)


