import os
import asyncio
from datetime import datetime, timedelta
import json

from modules.song import Song

LOG_FILENAME = "logfile.txt"
INDEX_FILENAME = "index.json"
FILENAME_FIELD = "filename"
TIMESTAMP_FIELD = "timestamp"
SELF = "SELF"
UPLOADED = "UPLOADED"


def add_to_index(filename: str):
    return {
        FILENAME_FIELD: filename,
        TIMESTAMP_FIELD: datetime.utcnow().isoformat(),
        UPLOADED: False,
    }


def rebuild_index():
    return {SELF: add_to_index(INDEX_FILENAME)}


def set_uploaded(obj):
    obj[UPLOADED] = True


def incomplete_download(filepath: str):
    return "webm" in filepath


class Storage:
    def __init__(self, DOWNLOAD_PATH) -> None:
        self.DOWNLOAD_PATH = DOWNLOAD_PATH
        self.logfile_lock = asyncio.Lock()
        self.logfile_path = os.path.join(self.DOWNLOAD_PATH, LOG_FILENAME)
        self.index_path = os.path.join(self.DOWNLOAD_PATH, INDEX_FILENAME)
        if os.path.exists(self.index_path):
            self.load_index()
        else:
            self.index = rebuild_index()
    
    async def add_to_logfile(self, log_string):
        async with self.logfile_lock:
            with open(self.logfile_path, "a", encoding="utf-8") as f:
                f.write(log_string + "\n")
                f.flush()
                
    def get_downloaded_filepaths(self):
        return [
            os.path.join(self.DOWNLOAD_PATH, file)
            for file in os.listdir(self.DOWNLOAD_PATH)
        ]

    def load_index(self):
        with open(self.index_path, "r") as f:
            self.index = json.load(f)
        return

    def save_index(self):
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)
        return

    def clean_files(self):
        updated_filepaths = [
            os.path.join(self.DOWNLOAD_PATH, v[FILENAME_FIELD])
            for v in self.index.values()
        ]
        for fp in self.get_downloaded_filepaths():
            if (fp not in updated_filepaths) and not incomplete_download(fp):
                os.remove(fp)
        return

    def clear_outdated(self):
        now = datetime.utcnow()
        delta = timedelta(days=3)
        self.index = {
            k: v
            for k, v in self.index.items()
            if (now - datetime.fromisoformat(v[TIMESTAMP_FIELD]) < delta)
            and (os.path.exists(os.path.join(self.DOWNLOAD_PATH, v[FILENAME_FIELD])))
        }
        self.index[SELF] = rebuild_index()[SELF]
        self.clean_files()
        return

    def clear_uploaded(self):
        self.index = {k: v for k, v in self.index.items() if not v[UPLOADED]}
        self.clean_files()
        return

    def reset_directory(self):
        for fp in self.get_downloaded_filepaths():
            os.remove(fp)
        self.index = rebuild_index()
        self.save_index()
        return

    def find_file(self, song: Song):
        if song.filename in os.listdir(self.DOWNLOAD_PATH):
            return True
        return False

    def get_index(self, song: Song):
        try:
            return self.index[song.youtube_id]
        except:
            return None

    def get_filepath(self, filename: str):
        return os.path.join(self.DOWNLOAD_PATH, filename)

    def finalize_filename(self, song: Song):
        extension = song.filename.split(".")[-1]
        new_filename = song.get_display_name() + "." + extension
        os.replace(self.get_filepath(song.filename), self.get_filepath(new_filename))
        song.filename = new_filename
        return

    def update_index(self, song: Song):
        self.index[song.youtube_id] = add_to_index(song.filename)
        return

    def mark_uploaded(self, song: Song):
        set_uploaded(self.index[song.youtube_id])
        return
