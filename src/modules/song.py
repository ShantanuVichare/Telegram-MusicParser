class Song:
    def __init__(self) -> None:
        self.name = None
        self.playlist = None
        self.spotify_id = None
        self.spotify_link = None
        self.artists = []
        self.duration = None
        self.youtube_id = None
        self.youtube_link = None
        self.filename = None
        self.retry_count = 0
        self.bit_rate = None
        self.message = None
        self.query = None
        self.logs = []

    def from_spotify_track(spotify_track):
        ret_obj = Song()
        ret_obj.name = spotify_track["name"]
        ret_obj.spotify_id = spotify_track["id"]
        ret_obj.spotify_link = spotify_track["external_urls"]
        ret_obj.artists = [artist["name"] for artist in spotify_track["artists"]]
        ret_obj.duration = spotify_track["duration_ms"] / 1000  # Store duration in secs
        return ret_obj

    def from_youtube_link(youtube_link):
        ret_obj = Song()
        ret_obj.youtube_link = youtube_link
        return ret_obj

    def from_query(query):
        ret_obj = Song()
        ret_obj.query = query + " audio"
        return ret_obj

    def get_search_query(self):
        if self.query is not None:
            return self.query
        return (
            self.name + " - Official Audio - " + ", ".join([artist for artist in self.artists])
        )

    def get_display_name(self) -> str:
        try:
            display_name = (
                self.name + " by " + ", ".join([artist for artist in self.artists])
            )
        except:
            display_name = self.filename
        return display_name

    def add_log(self, *args):
        log_str = " ".join([str(arg) for arg in args])
        self.logs.append(log_str)
        # For debugging
        print(log_str)

    def get_logs(self):
        return "\n-    ".join(self.logs)