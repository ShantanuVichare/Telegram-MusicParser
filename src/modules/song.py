class Song:
    def __init__(self) -> None:
        self.name = None
        self.spotify_id = None
        self.spotify_link = None
        self.artists = []
        self.youtube_id = None
        self.youtube_link = None
        self.external_name = None
        self.retry_count = 0
        self.bit_rate = None
        self.message = None
        self.query = None
    
    def from_spotify_track(spotify_track):
        ret_obj = Song()
        ret_obj.name = spotify_track['name']
        ret_obj.spotify_id = spotify_track['id']
        ret_obj.spotify_link = spotify_track['external_urls']
        ret_obj.artists = [artist['name'] for artist in spotify_track['artists']]
        return ret_obj

    def from_youtube_link(youtube_link):
        ret_obj = Song()
        ret_obj.youtube_link = youtube_link
        return ret_obj

    def from_query(query):
        ret_obj = Song()
        ret_obj.query = query
        return ret_obj

    def get_search_query(self):
        if self.query is not None:
            return self.query
        return self.name + ' - Audio Lyrics - ' + ', '.join([artist for artist in self.artists])

    def get_display_name(self) -> str:
        try:
            display_name = self.name + ' by ' + ', '.join([artist for artist in self.artists])
        except:
            if self.external_name is not None:
                display_name = self.external_name
            else:
                display_name = '...'
        
        return display_name
