
# import threading
from youtube_dl import YoutubeDL

from modules.song import Song

class Downloader:
    def __init__(self,DOWNLOAD_PATH: str, logger=print) -> None:
        self.DOWNLOAD_PATH = DOWNLOAD_PATH
        # self.lock = threading.Lock()
        self.max_retries = 3
        self.logging_func = logger
        self.codec = 'mp3' # mp3 supports Embedding thumbnail
        class MyLogger(object):
            def debug(self, msg):
                # logger('DEBUG - ' + msg)
                pass

            def warning(self, msg):
                # logger('WARN - ' + msg)
                pass

            def error(self, msg):
                logger('ERROR - ' + msg)
        self.ydl_opts = {
            # 'quiet': True,
            # 'writethumbnail': True,
            'age_limit': 30,
            'nocheckcertificate': True,
            'format': 'bestaudio/best',
            'outtmpl': self.DOWNLOAD_PATH+'%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.codec,
                'preferredquality': '256',},
                # {'key': 'EmbedThumbnail'}
            ],
            'logger': MyLogger(),
            'prefer_ffmpeg': True,
            # 'ffmpeg_location': './'
        }
    
    def retrieve_youtube_id(self, song: Song) -> bool:
        
        def get_best_match(results, song: Song) :
            best_match = results[0]
            if (song.duration is not None):
                d = song.duration
                d_diff = 1000000
                for v in results:
                    if abs(v['duration']-d) < d_diff:
                        d_diff = abs(v['duration']-d)
                        best_match = v
            return best_match

        with YoutubeDL(self.ydl_opts) as ydl:
            if song.youtube_link is not None:
                video = ydl.extract_info(song.youtube_link, download=False)
            else:
                results = ydl.extract_info(f"ytsearch{10}:{song.get_search_query()}", download=False)['entries']
                video = get_best_match(results, song)
            video['ext'] = self.codec
            filename = ydl.prepare_filename(video)
        song.youtube_id = video['id']
        song.external_name = filename[len(self.DOWNLOAD_PATH):]
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

