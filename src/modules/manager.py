
import os
import time
import threading
from typing import List
from telegram import ChatAction
from telegram.ext.callbackcontext import CallbackContext
from telegram.message import Message
from telegram.update import Update

from constants import SPOTIFY_ALBUM, SPOTIFY_PLAYLIST, SPOTIFY_TRACK, YOUTUBE_VIDEO, YOUTUBE_SHORT

from modules.spotify import Spotify
from modules.song import Song
from modules.downloader import Downloader
from modules.storage import Storage

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH')

if not os.path.exists(DOWNLOAD_PATH):
    print('path:' + DOWNLOAD_PATH + ' does not exist')
    os.mkdir(DOWNLOAD_PATH)
    print('path:' + DOWNLOAD_PATH + ' created successfully')

class Manager:
    def __init__(self,update: Update,context: CallbackContext,upload: bool=True) -> None:
        self.lock = threading.Lock()
        self.thread_access = threading.BoundedSemaphore(value=8)
        self.update = update
        self.context = context
        self.songs: List[Song] = []
        self.threads: List[threading.Thread] = []
        self.upload_to_chat = upload
        self.storage = Storage(DOWNLOAD_PATH)
        self.spotify = Spotify(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    def initialize_from_config(self,request_link:str=None,query:str=None,interact:bool=True) -> Message:
        msg = None
        if query is not None:
            self.songs += [Song.from_query(query)]
            if interact : msg = self.interact(text="Identified a search query")
        elif SPOTIFY_TRACK in request_link:
            self.songs += [self.spotify.get_song(song_link=request_link)]
            if interact : msg = self.interact(text="Identified a Spotify track")
        elif SPOTIFY_PLAYLIST in request_link:
            self.songs += self.spotify.get_playlist(playlist_link=request_link)
            if interact : msg = self.interact(text="Identified a Spotify playlist")
        elif SPOTIFY_ALBUM in request_link:
            self.songs += self.spotify.get_album(album_link=request_link)
            if interact : msg = self.interact(text="Identified a Spotify album")
        elif (YOUTUBE_VIDEO in request_link) or (YOUTUBE_SHORT in request_link):
            self.songs += [Song.from_youtube_link(youtube_link=request_link)]
            if interact : msg = self.interact(text="Identified a YouTube video")
        return msg

    def begin(self,request_link:str=None,query:str=None, retry_links:List[str]=[]):

        # TO-DO: Convert to config object
        if len(retry_links) > 0:
            msg = self.interact(text=f"Retrying {len(retry_links)} songs")
            for retry_link in retry_links : self.initialize_from_config(request_link=retry_link,interact=False)
        else:
            msg = self.initialize_from_config(request_link,query)
        if msg is None:
            self.context.bot.send_message(chat_id=self.update.effective_chat.id, text="Invalid URL")
            return
        
        self.storage.clear_outdated()

        if (len(self.songs)>1): msg = self.interact(msg=msg, text="Downloading {} songs".format(len(self.songs)))

        for song in self.songs:
            t = threading.Thread(target=Manager.my_thread, args=(self,song))
            t.start()
            self.threads.append(t)

        try:
            while any([t.is_alive() for t in self.threads]):
                time.sleep(2)
                if (len(self.songs)>1): msg = self.interact(msg=msg,text="Remaining songs {}/{}".format(sum([t.is_alive() for t in self.threads]),len(self.songs)),action=ChatAction.TYPING)
        except:
            print("Updating failed!")

        # Ensuring completion of threads
        t: threading.Thread
        for t in self.threads:
            t.join()
        
        msg.delete()
        if self.upload_to_chat:
            if (len(self.songs)>1): self.interact(text="Retrieved {}/{} songs".format(len([True for song in self.songs if song.message=='Upload completed']),len(self.songs)))
        else:
            if (len(self.songs)>1): self.interact(text="Downloaded {}/{} songs".format(len([True for song in self.songs if song.message=='Download completed']),len(self.songs)))
        
        print('Songs\' final Message:\n','\n\t'.join([song.message+' - '+song.get_display_name() for song in self.songs]))

        self.storage.save_index()
        return

    def my_thread(myself, song: Song):

        myself.thread_access.acquire()
        logs = []
        log = logs.append
        downloader = Downloader(DOWNLOAD_PATH, logger=log)
        log("Started: "+song.get_display_name())
        try:
            msg = myself.interact(text="Searching: "+song.get_display_name(),action=ChatAction.TYPING)
            log("Found: "+song.get_display_name())

            # Update YouTube data
            downloader.retrieve_youtube_id(song)
            log("Retreived YouTube ID: "+song.youtube_id)

            # Check Index for pre-downloaded files
            if myself.storage.find_file(song):
                log("Indexed file found: "+str(myself.storage.get_index(song)))
            else:
                # Ensure storage availability
                myself.storage.clear_uploaded()

                # Initiate Download
                if song.retry_count < downloader.max_retries:
                    log("Downloader try: "+str(song.retry_count))
                    downloader.download(song)

                # Verify Initiation
                if song.message == "Download couldn't start":
                    log("Download couldn't start: "+song.get_display_name())
                    msg = myself.interact(msg=msg,text="Download couldn't start: "+song.get_display_name(),action=ChatAction.TYPING)
                    raise Exception("Download couldn't start")
                elif song.message == "Download started":
                    log("Download started: "+song.get_display_name())
                    msg = myself.interact(msg=msg,text="Download started: "+song.get_display_name(),action=ChatAction.TYPING)

                # Download Timeout
                start_time = time.time()
                time_emojis = ['🕛','🕐','🕑','🕒','🕓','🕔','🕕','🕖','🕗','🕘','🕙','🕚']
                time_emoji_ind = 0
                while not myself.storage.find_file(song):
                    if time.time() - start_time >= 300: # Timeout of 5 mins
                        break
                    msg = myself.interact(msg=msg,text=f"Downloading ({time_emojis[time_emoji_ind]}) : {song.get_display_name()}",action=ChatAction.TYPING)
                    time.sleep(2)
                    time_emoji_ind = (time_emoji_ind + 1) % len(time_emojis)

            # Verify completion
            if not myself.storage.find_file(song):
                song.message = "Download couldn't complete"
                log("Download couldn't complete: "+song.get_display_name())
                msg = myself.interact(msg=msg,text="Download couldn't complete: "+song.get_display_name(),action=ChatAction.TYPING)
                raise Exception("Download couldn't complete")

            # Succesful Download
            song.message = 'Download completed'
            log("Download completed: "+song.get_display_name())
            myself.storage.update_index(song)
            log("Index Updated: "+song.get_display_name())
            msg = myself.interact(msg=msg,text="Download completed! Now Uploading: "+song.get_display_name(),action=ChatAction.UPLOAD_AUDIO,filename=myself.storage.get_filepath(song))
            # myself.context.bot.send_document(chat_id=myself.update.effective_chat.id, document=open(filename, 'rb'))
            if myself.upload_to_chat:
                myself.storage.mark_uploaded(song)
                song.message = 'Upload completed'
                log("Uploaded: "+song.get_display_name())
            myself.storage.save_index()
            msg.delete()
        except Exception as e :
            msg = myself.interact(msg=msg,text="Download failed for: "+song.get_display_name(),action=ChatAction.TYPING)
            print("Exception:",e)
            print_logs = "\n-    ".join(logs)
            print(f"Thread failed for Song: {song.get_display_name()}\nLogs:\n{print_logs}")
        
        myself.thread_access.release()
        return
    
    def interact(self,msg: Message=None,text=None,action=None,filename=None):
        self.lock.acquire()
        if msg is not None:
            if (text is not None) and (text != msg.text):
                # print('Text:',text,'Msg.text:',msg.text)
                msg = msg.edit_text(text)
        elif text is not None: 
            msg = self.context.bot.send_message(chat_id=self.update.effective_chat.id, text=text)

        if action is not None:
            self.context.bot.send_chat_action(chat_id=self.update.effective_chat.id, action=action)
        
        self.lock.release()

        if (self.upload_to_chat is True) and (filename is not None):
            self.context.bot.send_document(chat_id=self.update.effective_chat.id, timeout=600, document=open(filename, 'rb'))
            # self.context.bot.send_media_group()
        # self.lock.release()
        return msg
