# import asyncio
# from youtube_dl import YoutubeDL
import os
from yt_dlp import YoutubeDL

from modules.song import Song


class Downloader:
    def __init__(self, DOWNLOAD_PATH: str, logger=print) -> None:
        self.DOWNLOAD_PATH = DOWNLOAD_PATH
        # self.lock = asyncio.Lock()
        self.max_retries = 3
        self.logging_func = logger
        self.codec = "mp3"  # mp3 supports Embedding thumbnail

        class MyLogger(object):
            def debug(self, msg):
                # logger('DEBUG - ' + msg)
                pass

            def warning(self, msg):
                # logger('WARN - ' + msg)
                pass

            def error(self, msg):
                logger("ERROR - " + msg)

        self.ydl_opts_download = {
            # 'quiet': True,
            # 'writethumbnail': True,
            "age_limit": 30,
            "nocheckcertificate": True,
            "format": "bestaudio/best",
            "outtmpl": self.DOWNLOAD_PATH + "%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.codec,
                    "preferredquality": "192",
                },
                # {'key': 'EmbedThumbnail'}
            ],
            "logger": MyLogger(),
            "prefer_ffmpeg": True,
            # 'ffmpeg_location': './'
        }
        self.ydl_opts_search = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "format": "bestaudio/best",
            "outtmpl": "%(title)s.%(ext)s",
        }

    async def retrieve_youtube_id(self, song: Song) -> bool:

        def get_best_match(results, song: Song):
            best_match = results[0]
            if song.duration is not None:
                d = song.duration
                d_diff = 1000000
                for v in results:
                    if v["duration"] and (abs(v["duration"] - d) < d_diff):
                        d_diff = abs(v["duration"] - d)
                        best_match = v
            return best_match

        try:
            with YoutubeDL(self.ydl_opts_search) as ydl:
                if song.youtube_link is not None:
                    video = ydl.extract_info(song.youtube_link, download=False)
                else:
                    results = ydl.extract_info(
                        f"ytsearch{10}:{song.get_search_query()}", download=False
                    )["entries"]
                    video = get_best_match(results, song)
                video["ext"] = self.codec
            song.youtube_id = video["id"]
            song.filename = ydl.prepare_filename(video)
            song.message = "Search successful"
            self.logging_func('Search for "' + song.get_display_name() + '" successful!')
        except:
            song.message = "Search failed"
            self.logging_func('Search for "' + song.get_display_name() + '" failed!')
        return

    async def download(self, song: Song, outfilepath: str) -> bool:
        file_downloaded = False
        # await self.lock.acquire()
        try:
            outfilepath = outfilepath.replace(self.codec, "%(ext)s")
            file_ydl_opts = {**self.ydl_opts_download}
            file_ydl_opts["outtmpl"] = outfilepath
            with YoutubeDL(file_ydl_opts) as ydl:
                ydl.download([song.youtube_id])
            song.message = "Download started"
            file_downloaded = True
            self.logging_func('Download for "' + song.get_display_name() + '" Started!')
        except:
            song.message = "Download couldn't start"
            file_downloaded = False
            self.logging_func(
                'Download for "' + song.get_display_name() + '" couldnt start!'
            )

        if not file_downloaded:
            song.retry_count += 1
            # self.lock.release()
            return False
        # self.lock.release()
        return True
