
# import threading
from youtube_dl import YoutubeDL

from modules.song import Song

class Downloader:
    def __init__(self,DOWNLOAD_PATH, logging_func=print) -> None:
        self.DOWNLOAD_PATH = DOWNLOAD_PATH
        # self.lock = threading.Lock()
        self.max_retries = 3
        self.logging_func = logging_func
        self.codec = 'mp3' # mp3 supports Embedding thumbnail
        class MyLogger(object):
            def debug(self, msg):
                # logging_func('DEBUG - ' + msg)
                pass

            def warning(self, msg):
                # logging_func('WARN - ' + msg)
                pass

            def error(self, msg):
                logging_func('ERROR - ' + msg)
        self.ydl_opts = {
        #     'quiet': True,
        #     'writethumbnail': True,
            'age_limit': 30,
            'nocheckcertificate': True,
            'format': 'bestaudio/best',
            'outtmpl': DOWNLOAD_PATH+'%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.codec,
                'preferredquality': '256',},
        #     {'key': 'EmbedThumbnail'}
            ],
            'logger': MyLogger(),
            'prefer_ffmpeg': True,
        #     'ffmpeg_location': './'
        }
    
    def retrieve_youtube_id(self, song: Song) -> bool:

        if song.youtube_link is not None:
            with YoutubeDL(self.ydl_opts) as ydl:
                video = ydl.extract_info(song.youtube_link, download=False)
        else:
            query = song.get_search_query()
            with YoutubeDL(self.ydl_opts) as ydl:
                video = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        song.youtube_id = video['id']
        song.external_name = video['title']+'.'+self.codec
        return

    def download(self,song: Song) -> bool:
        file_downloaded = False
        # self.lock.acquire()
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([song.youtube_id])
            song.message = 'Download started'
            file_downloaded = True
            self.logging_func('Download for "'+song.get_display_name()+'" Started!')
        except:
            song.message = "Download couldn't start"
            file_downloaded = False
            self.logging_func('Download for "'+song.get_display_name()+'" couldnt start!')

        if not file_downloaded:
            song.retry_count += 1
            # self.lock.release()
            return False
        # self.lock.release()
        return True

