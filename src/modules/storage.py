import os
from datetime import datetime, timedelta
import json

from modules.song import Song

INDEX_FILENAME = 'index.json'
FILENAME_FIELD = 'filename'
TIMESTAMP_FIELD = 'timestamp'
SELF = 'SELF'

class Storage:
    def __init__(self, DOWNLOAD_PATH) -> None:
        self.DOWNLOAD_PATH = DOWNLOAD_PATH
        self.index_path = os.path.join(self.DOWNLOAD_PATH,INDEX_FILENAME)
        if os.path.exists(self.index_path):
            self.load_index()
        else:
            self.index = {SELF:{FILENAME_FIELD: INDEX_FILENAME, TIMESTAMP_FIELD: datetime.utcnow().isoformat()}}

    def get_downloaded_filepaths(self):
        return [os.path.join(self.DOWNLOAD_PATH,file) for file in os.listdir(self.DOWNLOAD_PATH)]
    
    def load_index(self):
        with open(self.index_path,'r') as f:
            self.index = json.load(f)
        return

    def save_index(self):
        with open(self.index_path, "w") as f: 
            json.dump(self.index, f) 
        return
    
    def clean_files(self):
        now = datetime.utcnow()
        delta = timedelta(days=2)
        self.index = {k:self.index[k] for k in self.index if now - datetime.fromisoformat(self.index[k][TIMESTAMP_FIELD]) < delta }
        self.index[SELF] = {FILENAME_FIELD: INDEX_FILENAME, TIMESTAMP_FIELD: datetime.utcnow().isoformat()}
        updated_filepaths = [os.path.join(self.DOWNLOAD_PATH, self.index[k][FILENAME_FIELD]) for k in self.index]
        for fp in self.get_downloaded_filepaths():
            if fp not in updated_filepaths: os.remove(fp)
        
        return

    def reset_directory(self):
        for fp in self.get_downloaded_filepaths(self.DOWNLOAD_PATH): os.remove(fp)
        self.index = {SELF:{FILENAME_FIELD: INDEX_FILENAME, TIMESTAMP_FIELD: datetime.utcnow().isoformat()}}
        self.save_index()
        return

    def find_file(self, song: Song):
        if (song.external_name in os.listdir(self.DOWNLOAD_PATH)):
            return True
        return False

    def get_index(self,song: Song):
        try:
            return self.index[song.youtube_id]
        except:
            return None

    def get_filepath(self, song: Song):
        return os.path.join(self.DOWNLOAD_PATH,song.external_name)

    def update_index(self,song: Song):
        self.index[song.youtube_id] = {FILENAME_FIELD: song.external_name, TIMESTAMP_FIELD: datetime.utcnow().isoformat()}
        return
