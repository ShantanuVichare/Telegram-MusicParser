import os
import uuid
import asyncio
from datetime import datetime, timedelta
import json
import zipfile

from modules.song import Song

LOG_FILENAME = "logfile.txt"
INDEX_FILENAME = "index.json"
USERS_FILENAME = "users.json"
FILENAME_FIELD = "filename"
TIMESTAMP_FIELD = "timestamp"
UPLOADED_FIELD = "uploaded"


def add_to_index(filename: str):
    return {
        FILENAME_FIELD: filename,
        TIMESTAMP_FIELD: datetime.utcnow().isoformat(),
        UPLOADED_FIELD: False,
    }


def rebuild_index(base_index={}):
    return {
        **base_index,
        "INDEX": add_to_index(INDEX_FILENAME),
        "LOG": add_to_index(LOG_FILENAME),
    }


def set_uploaded(obj):
    obj[UPLOADED_FIELD] = True


def incomplete_download(filepath: str):
    return "webm" in filepath


class Storage:
    def __init__(self, storage_location) -> None:
        self.storage_location = storage_location
        self.logfile_lock = asyncio.Lock()
        self.logfile_path = os.path.join(self.storage_location, LOG_FILENAME)
        self.usersfile_lock = asyncio.Lock()
        self.usersfile_path = os.path.join(self.storage_location, USERS_FILENAME)
        if os.path.exists(self.usersfile_path):
            with open(self.usersfile_path, "w") as f:
                self.usersdict = json.load(f)
        else:
            self.usersdict = {}
        
        self.index_path = os.path.join(self.storage_location, INDEX_FILENAME)
        if os.path.exists(self.index_path):
            self.index = self.load_index()
        else:
            self.index = rebuild_index()
    
    def get_location(self):
        return self.storage_location
    
    async def add_to_logfile(self, log_string):
        async with self.logfile_lock:
            with open(self.logfile_path, "a", encoding="utf-8") as f:
                f.write(log_string + "\n")
                f.flush()
    
    async def get_logs(self):
        async with self.logfile_lock:
            with open(self.logfile_path, "r", encoding="utf-8") as f:
                return f.read()
    
    async def add_to_usersfile(self, user_id, chat_id):
        async with self.usersfile_lock:
            if user_id not in self.usersdict:
                self.usersdict[user_id] = [chat_id]
            elif chat_id not in self.usersdict[user_id]:
                self.usersdict[user_id].append(chat_id)
            with open(self.usersfile_path, "w") as f:
                json.dump(self.usersdict, f, indent=2)
                
    def get_downloaded_filepaths(self):
        return [
            os.path.join(self.storage_location, file)
            for file in os.listdir(self.storage_location)
        ]

    def load_index(self):
        with open(self.index_path, "r") as f:
            return json.load(f)

    def save_index(self):
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)
        return

    def clean_files(self):
        updated_filepaths = [
            os.path.join(self.storage_location, v[FILENAME_FIELD])
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
            and (os.path.exists(os.path.join(self.storage_location, v[FILENAME_FIELD])))
        }
        self.index = rebuild_index(self.index)
        self.clean_files()
        return

    def clear_uploaded(self):
        self.index = {k: v for k, v in self.index.items() if not v[UPLOADED_FIELD]}
        self.clean_files()
        return

    def reset_directory(self):
        for fp in self.get_downloaded_filepaths():
            os.remove(fp)
        self.index = rebuild_index()
        self.save_index()
        return

    def find_file(self, song: Song):
        if song.filename in os.listdir(self.storage_location):
            return True
        return False

    def get_index(self, song: Song):
        try:
            return self.index[song.youtube_id]
        except:
            return None

    def get_filepath(self, filename: str):
        return os.path.join(self.storage_location, filename)
    
    def get_zipped(self, filenames):
        filepaths = [self.get_filepath(filename) for filename in filenames]
        zip_filename = uuid.uuid4().hex + ".zip"
        zip_filename = self.get_filepath(zip_filename)
        with zipfile.ZipFile(zip_filename, "w") as zip_file:
            for filepath,filename in zip(filepaths,filenames):
                zip_file.write(filepath, filename)
        return zip_filename

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
