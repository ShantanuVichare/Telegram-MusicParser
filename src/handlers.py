
import os
import time
import traceback
import random
from typing import List

from telegram import Update, BotCommand
from telegram.ext import CallbackContext
from telegram.constants import ChatAction

from constants import RANDOM_RESPONSES
from modules.manager import Manager

# import logging
# Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)


# inline_query = None

bot_commands = [
    BotCommand('start', 'Introduction to using the bot'),
    BotCommand('get', 'Tap and Hold to add <media_link>'),
    BotCommand('cache', 'Tap and Hold to add <media_link>'),
    BotCommand('search', 'Tap and Hold to add <search_query>'),
    BotCommand('help', 'List the supported link formats'),
]

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
async def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if len(context.args) == 1  and context.args[0] == "inline" :
        pass
    else :
        fname = update.message.from_user.first_name
        await update.message.reply_text('''
Hey {}, Welcome to Music Parser 🎶
✨Directly share your Spotify, YouTube links here 👇🏻

OR try the following:
📥 /download <download_link> to only download on server local storage
✅ /get <search_query> to search and download the first result
❔ /help to check supported link formats
        '''.format(fname))

async def help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('''
    Supported URL types:
    Spotify Tracks: https://open.spotify.com/track/XXXXXXXXXXXXXXXXXXXXXX
    Spotify Playlists: https://open.spotify.com/playlist/XXXXXXXXXXXXXXXXXXXXXX
    Spotify Albums: https://open.spotify.com/album/XXXXXXXXXXXXXXXXXXXXXX
    YouTube Videos: https://www.youtube.com/watch?v=XXXXXXXXXXX
    ''')

async def cache_only(update: Update, context: CallbackContext):
    """ To only download files on user directory """
    m = Manager(update,context,upload=False)
    for link in context.args:
        await m.begin(request_link=link) # TODO parallelize

async def generate_response(update: Update, context: CallbackContext):
    """Respond to user message."""
    user_text = update.message.text
    if ('open.spotify.com' in user_text) or ('youtube.com' in user_text) or ('youtu.be' in user_text) or (update.message.via_bot):
        m = Manager(update,context)
        is_query = update.message.via_bot and update.message.via_bot.is_bot
        if is_query :
            await m.begin(query=user_text)
    else:
        await update.message.reply_text(random.choice(RANDOM_RESPONSES))

async def get_media(update: Update, context: CallbackContext):
    """ Download and send files from link """
    if (len(context.args) == 0): return
    m = Manager(update,context)
    for link in context.args:
        await m.begin(request_link=link) # TODO parallelize

async def search(update: Update, context: CallbackContext):
    """Directly search and return retrieve the media"""
    if (len(context.args) == 0): return
    search_query = ' '.join(context.args)
    m = Manager(update,context)
    await m.begin(query=search_query)

async def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    await update.message.reply_text('I messed up bad 😅\nPlease contact my owner')
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    print(f"Failed command: {update.message.text}\nCaused error: {tb_string}")

async def inlinequery(update: Update, context: CallbackContext):
    """Handle the inline query."""
    inline_query = update.inline_query.query
    if ('open.spotify.com' in inline_query) or ('youtube.com' in inline_query):
        # update.inline_query.answer(results = [], switch_pm_text="Tap here to Download Now!", switch_pm_parameter="inline")
        pass

async def debug(update: Update, context: CallbackContext):
    """
    Send a message when the command /debug is issued.
    Just a testing command!
    """
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING, read_timeout=15)
    debugHandler = DebugCommandHandler(Manager(update, context))
    if len(context.args)>0:
        reply_command = debugHandler.get_reply_command(context.args[0])
        reply_text = reply_command(context.args[1:])
        await update.message.reply_text(reply_text)
    else:
        supported_cmds = debugHandler.get_display_commands()
        await update.message.reply_text(f"Supported commands:\n{supported_cmds}")
    return

class DebugCommandHandler :
    def __init__(self, manager: Manager) -> None:
        self.m = manager
        self.commands = {
            'list': self.list_files,
            'reset': self.reset_files,
            'execute': self.execute,
        }
    
    def get_display_commands(self) -> List[str]:
        return list(self.commands.keys())
    
    def get_reply_command(self, command_text: str):
        return self.commands[command_text]
    
    def execute(self, add_args) -> str:
        return os.popen(' '.join(add_args)).read()

    def list_files(self, add_args) -> str:
        return f"Path: {self.m.storage.DOWNLOAD_PATH}\nFiles: {os.listdir(self.m.storage.DOWNLOAD_PATH)}"

    def reset_files(self, add_args) -> str:
        self.m.storage.reset_directory()
        return self.list_files()

