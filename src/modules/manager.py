import asyncio
import os
import time
from typing import List, Tuple

from traceback import format_exception

from telegram.constants import ChatAction
from telegram.ext import CallbackContext
from telegram import Message, Update, InputMediaDocument, InputMediaAudio

from constants import (
    SPOTIFY_ALBUM,
    SPOTIFY_PLAYLIST,
    SPOTIFY_TRACK,
    YOUTUBE_VIDEO,
    YOUTUBE_SHORT,
)

from modules.spotify import Spotify
from modules.song import Song
from modules.downloader import Downloader
from modules.storage import Storage

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
DOWNLOAD_PATH = os.environ.get("DOWNLOAD_PATH")

if not os.path.exists(DOWNLOAD_PATH):
    print("path:" + DOWNLOAD_PATH + " does not exist")
    os.mkdir(DOWNLOAD_PATH)
    print("path:" + DOWNLOAD_PATH + " created successfully")


class Manager:
    def __init__(
        self, update: Update, context: CallbackContext, upload: bool = True
    ) -> None:
        self.download_sem = asyncio.BoundedSemaphore(5)
        self.update = update
        self.context = context
        self.upload_to_chat = upload
        self.combine_files = False
        self.storage = Storage(storage_location=DOWNLOAD_PATH)
        self.spotify = Spotify(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    async def initialize_media(
        self, possible_links: List[str] = None, query: str = None
    ) -> Tuple[List[Song], Message]:
        songs = []
        msg = None
        if query is not None:
            songs += [Song.from_query(query)]
            msg = await self.interact(text="Processing a search query")
        else:
            for link in possible_links:
                if SPOTIFY_TRACK in link:
                    songs += [self.spotify.get_song(song_link=link)]
                elif SPOTIFY_PLAYLIST in link:
                    songs += self.spotify.get_playlist(playlist_link=link)
                elif SPOTIFY_ALBUM in link:
                    songs += self.spotify.get_album(album_link=link)
                elif (YOUTUBE_VIDEO in link) or (YOUTUBE_SHORT in link):
                    songs += [Song.from_youtube_link(youtube_link=link)]
        songs = [song for song in songs if song is not None]
        if len(songs) > 0:
            msg = await self.interact(msg=msg, text=f"Processing {len(songs)} song(s)")
        # if len(songs) > 1:
        #     self.combine_files = True
        #     self.upload_to_chat = False
        return (songs, msg)

    async def process_songs(self, songs: List[Song], prev_msg: Message = None):

        self.storage.clear_outdated()

        msg = await self.interact(
            msg=prev_msg, text="Downloading {} song(s)".format(len(songs))
        )

        tasks = set()
        for song in songs:
            task = asyncio.create_task(self.process_song(song))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

        task_exec_future = asyncio.gather(*tasks)
        n_active_tasks = lambda: sum([not t.done() for t in tasks])
        try:
            while n_active_tasks() > 0:
                await asyncio.sleep(1)
                if len(songs) > 1:
                    msg = await self.interact(
                        msg=msg,
                        text="Remaining songs {}/{}".format(
                            n_active_tasks(), len(songs)
                        ),
                        action=ChatAction.TYPING,
                    )
        except:
            print("Updating failed!")

        # Ensuring completion of threads
        await task_exec_future

        if self.upload_to_chat:
            incomplete_songs = [
                song for song in songs if song.message != "Upload completed"
            ]
        else:
            incomplete_songs = [
                song for song in songs if song.message != "Download completed"
            ]

        # retry_msg = None
        # if len(incomplete_songs) > 0:
        #     retry_msg = await self.interact(
        #         text="Retrying {} songs".format(len(incomplete_songs))
        #     )

        if self.combine_files:
            msg = await self.interact(
                msg=msg,
                text="Uploading {} songs".format(len(songs) - len(incomplete_songs)),
                action=ChatAction.UPLOAD_DOCUMENT,
                filename=self.storage.get_zipped([song.filename for song in songs if song.message == "Download completed"]),
                # group_filenames=[self.storage.get_filepath(song.filename) for song in songs  if song.message == "Download completed"],
            )
        else:
            await self.interact(
                text="Downloaded {}/{} songs".format(
                    len(songs) - len(incomplete_songs), len(songs)
                )
            )

        print(
            "Songs' final Message:\n\t",
            "\n\t".join(
                [str(song.message) + " - " + song.get_display_name() for song in songs]
            ),
        )
        
        await msg.delete()

        self.storage.save_index()
        return incomplete_songs

    async def process_song(self, song: Song):

        await self.download_sem.acquire()
        log_fn = song.add_log
        msg = None
        try:
            # Update YouTube data
            downloader = Downloader(DOWNLOAD_PATH, logger=log_fn)
            await downloader.retrieve_youtube_id(song)
            
            if song.query is not None:
                log_fn(f"Searching: {song.query}")
            
            log_fn(f"Started: {song.get_display_name()}\tRetreived YouTube ID: {song.youtube_id}")
            msg = await self.interact(
                text="Searching: " + song.get_display_name(), action=ChatAction.TYPING
            )

            # Check Index for pre-downloaded files
            if self.storage.find_file(song):
                log_fn("Indexed file found: " + str(self.storage.get_index(song)))
            else:
                # Ensure storage availability
                # self.storage.clear_uploaded()

                # Initiate Download
                if song.retry_count < downloader.max_retries:
                    log_fn("Downloader try: " + str(song.retry_count))
                    await downloader.download(song, self.storage.get_filepath(song.filename))

                # Verify Initiation
                if song.message == "Download couldn't start":
                    log_fn("Download couldn't start: " + song.get_display_name())
                    msg = await self.interact(
                        msg=msg,
                        text="Download couldn't start: " + song.get_display_name(),
                        action=ChatAction.TYPING,
                    )
                    raise Exception("Download couldn't start")
                elif song.message == "Download started":
                    log_fn("Download started: " + song.get_display_name())
                    msg = await self.interact(
                        msg=msg,
                        text="Download started: " + song.get_display_name(),
                        action=ChatAction.TYPING,
                    )

                # Download Timeout
                start_time = time.time()
                time_emojis = ["🕛","🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚",]
                time_emoji_ind = 0
                while not self.storage.find_file(song):
                    if time.time() - start_time >= 300:  # Timeout of 5 mins
                        break
                    msg = await self.interact(
                        msg=msg,
                        text=f"Downloading ({time_emojis[time_emoji_ind]}) : {song.get_display_name()}",
                        action=ChatAction.TYPING,
                    )
                    await asyncio.sleep(2)
                    time_emoji_ind = (time_emoji_ind + 1) % len(time_emojis)

            # Verify completion
            if not self.storage.find_file(song):
                song.message = "Download couldn't complete"
                log_fn("Download couldn't complete: " + song.get_display_name())
                msg = await self.interact(
                    msg=msg,
                    text="Download couldn't complete: " + song.get_display_name(),
                    action=ChatAction.TYPING,
                )
                raise Exception("Download couldn't complete")

            # Succesful Download - Rename and add to index
            # self.storage.finalize_filename(song)
            song.message = "Download completed"
            log_fn("Download completed: " + song.get_display_name())
            self.storage.update_index(song)
            log_fn("Index Updated: " + song.get_display_name())
            msg = await self.interact(
                msg=msg,
                text="Download completed: " + song.get_display_name(),
            )

            # Send to TG servers
            if self.upload_to_chat:
                msg = await self.interact(
                    msg=msg,
                    text="Uploading: " + song.get_display_name(),
                    action=ChatAction.UPLOAD_DOCUMENT,
                    filename=self.storage.get_filepath(song.filename),
                )
                self.storage.mark_uploaded(song)
                song.message = "Upload completed"
                log_fn("Uploaded: " + song.get_display_name())
            self.storage.save_index()
            await msg.delete()
        except Exception as e:
            exception_string = "".join(format_exception(
                None, e, e.__traceback__
            ))
            log_fn("Exception:", exception_string)
            song_logs = song.get_logs()
            print(
                f"Thread failed for Song: {song.get_display_name()}\nLogs:\n{song_logs}"
            )
            await self.storage.add_to_logfile(song_logs)
            msg = await self.interact(
                msg=msg,
                text="Download failed for: " + song.get_display_name(),
                action=ChatAction.TYPING,
            )
        finally:
            self.download_sem.release()

        return

    async def interact(
        self, msg: Message = None, text=None, action=None, filename=None, group_filenames=None,
    ):
        # self.lock.acquire()
        if msg is not None:
            if (text is not None) and (text != msg.text):
                # print('Text:',text,'Msg.text:',msg.text)
                msg = await msg.edit_text(text)
        elif text is not None:
            msg = await self.context.bot.send_message(
                chat_id=self.update.effective_chat.id, text=text,
                disable_notification=True,
            )

        if action is not None:
            await self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id, action=action
            )

        # self.lock.release()

        if filename:
            document = open(filename, "rb")
            await self.context.bot.send_document(
                chat_id=self.update.effective_chat.id,
                read_timeout=600,
                write_timeout=600,
                document=document,
            )
        if group_filenames:
            media=[
                InputMediaAudio(open(filename, "rb"))
                for filename in group_filenames
            ]
            await self.context.bot.send_media_group(
                chat_id=self.update.effective_chat.id,
                read_timeout=600,
                write_timeout=600,
                media=media
            )
        # self.lock.release()
        return msg
