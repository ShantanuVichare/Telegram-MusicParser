
import os
import time
import random

from telegram import Update, BotCommand, ChatAction
from telegram.ext import CallbackContext

from constants import RANDOM_RESPONSES
from modules.manager import Manager

# import logging
# Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)


# inline_query = None

bot_commands = [
    BotCommand('start', 'Introduction to using the bot'),
    BotCommand('help', 'List the supported link formats'),
    BotCommand('download', 'Tap and Hold to add <download_link>'),
    BotCommand('get', 'Tap and Hold to add <search_query>'),
]

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if len(context.args) == 1  and context.args[0] == "inline" :
        pass
    else :
        update.message.reply_text('''
Welcome to Music Parser 🎶
✨Directly share your Spotify, YouTube links here 🤘🏻

OR try the following:
📥 /download <download_link> to only download on server local storage
✅ /get <search_query> to search and download the first result
❔ /help to check supported link formats
        ''')

def help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('''
    Supported URL types:
    Spotify Tracks: https://open.spotify.com/track/XXXXXXXXXXXXXXXXXXXXXX
    Spotify Playlists: https://open.spotify.com/playlist/XXXXXXXXXXXXXXXXXXXXXX
    Spotify Albums: https://open.spotify.com/album/XXXXXXXXXXXXXXXXXXXXXX
    YouTube Videos: https://www.youtube.com/watch?v=XXXXXXXXXXX
    ''')

def debug(update: Update, context: CallbackContext):
    """
    Send a message when the command /debug is issued.
    Just a testing command!
    """
    update.message.reply_text(os.getcwd())
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING, timeout=15)
    if len(context.args)>0: DebugCommandHandler(Manager(update, context), update.message.reply_text, context.args[0])

def download_only(update: Update, context: CallbackContext):
    """ To only download files on user directory """
    m = Manager(update,context,upload=False)
    for link in context.args:
        m.begin(link)

def generate_response(update: Update, context: CallbackContext):
    """Respond to user message."""
    user_text = update.message.text
    if ('open.spotify.com' in user_text) or ('youtube.com' in user_text) or ('youtu.be' in user_text) or (update.message.via_bot):
        m = Manager(update,context)
        is_query = update.message.via_bot and update.message.via_bot.is_bot
        m.begin(user_text, is_query)
    else:
        update.message.reply_text(random.choice(RANDOM_RESPONSES))

def get_media(update: Update, context: CallbackContext):
    """Directly search and return retrieve the media"""
    user_text = update.message.text
    if (len(context.args) == 0): return
    search_query = ' '.join(context.args)
    m = Manager(update,context)
    m.begin(search_query, is_query=True)

def search(update: Update, context: CallbackContext):
    update.message.reply_html('Were you looking for <b>/get</b> ?')

def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    update.message.reply_text('I messed up bad 😅\nPlease contact my owner')
    print(f"Message Text: {update.message.text}\nCaused error: {context.error}")
    # logger.warning(f"Message Text: {update.message.text}\nCaused error: {context.error}")

def inlinequery(update: Update, context: CallbackContext):
    """Handle the inline query."""
    inline_query = update.inline_query.query
    if ('open.spotify.com' in inline_query) or ('youtube.com' in inline_query):
        # update.inline_query.answer(results = [], switch_pm_text="Tap here to Download Now!", switch_pm_parameter="inline")
        pass

class DebugCommandHandler :
    def __init__(self, manager: Manager, reply_func, command_text: str) -> None:
        self.m = manager
        commands = {
            'list': self.list_files,
            'reset': self.reset_files
        }
        reply_text = commands[command_text]()
        reply_func(reply_text)
    
    def list_files(self) -> str:
        return os.listdir(self.m.storage.DOWNLOAD_PATH)

    def reset_files(self) -> str:
        self.m.storage.reset_directory()
        return os.listdir(self.m.storage.DOWNLOAD_PATH)

