

import spotipy

from modules.song import Song

class Spotify:
    def __init__(self,SPOTIFY_CLIENT_ID,SPOTIFY_CLIENT_SECRET) -> None:
        auth_key = spotipy.oauth2.SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        )
        self.client = spotipy.Spotify(auth_manager=auth_key)
    
    def get_album(self, album_link):
        spotify = self.client
        songs = spotify.album(album_link)['tracks']['items']
        songs = [Song.from_spotify_track(song) for song in songs]
        return songs

    def get_playlist(self, playlist_link=None, playlist_name='Daily Mix'):
        spotify = self.client
        if playlist_link is None:
            results = spotify.search(q=playlist_name, type='playlist')
            results = [(res['name']+' by '+res['owner']['display_name'],res['id'],res['external_urls']) for res in results['playlists']['items']]
            playlist_link = results[0][2]['spotify']
        
        songs = spotify.playlist(playlist_link)['tracks']['items']
        songs = [Song.from_spotify_track(song['track']) for song in songs]
        
        return songs
    
    def get_song(self, song_link=None, song_name=None):
        spotify = self.client
        while song_link is None:
            if song_name == None:
                song_name = input('Enter song search query:')
            results = spotify.search(q=song_name, type='track')
            songs = [Song.from_spotify_track(song) for song in results['tracks']['items']]
            print('\n'.join([str(i+1)+'. '+ song.get_display_name() for i,song in enumerate(songs)]))
            selection = int(input('Select from the list:(Enter 0 for retrying)'))
            if 0 < selection <= len(songs):
                return [songs[selection-1]]
                
        return [Song.from_spotify_track(spotify.track(song_link))]
