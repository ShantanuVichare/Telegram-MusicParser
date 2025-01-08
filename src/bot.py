import asyncio
import os
import time
from multiprocessing import Process

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
)
import telegram.ext.filters as Filters
from telegram.constants import SUPPORTED_WEBHOOK_PORTS

from webshell import shell_process
import handlers

from constants import TEMP_DIR

WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", 80))
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")


def validate():
    assert (
        WEBHOOK_PORT in SUPPORTED_WEBHOOK_PORTS
    ), f"Supported ports are f{SUPPORTED_WEBHOOK_PORTS}"


def bot_process():
    """Start the bot."""

    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands(handlers.bot_commands)

    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", handlers.start, block=False))
    application.add_handler(CommandHandler("help", handlers.help, block=False))
    
    application.add_handler(CommandHandler("debug", handlers.debug, block=False))
    application.add_handler(CommandHandler("user", handlers.user, block=False))

    application.add_handler(CommandHandler("cache", handlers.cache_only, block=False))

    application.add_handler(CommandHandler("get", handlers.get_media, block=False))

    application.add_handler(CommandHandler("search", handlers.search, block=False))
    # application.add_handler(CallbackQueryHandler())

    # # on noncommand i.e message - get a response
    application.add_handler(
        MessageHandler(Filters.TEXT, handlers.generate_response, block=False)
    )
    
    # Add a handler for document uploads
    application.add_handler(MessageHandler(Filters.Document.ALL, handlers.handle_file_upload))

    application.add_handler(InlineQueryHandler(handlers.inlinequery, block=False))

    # # log all errors
    application.add_error_handler(handlers.error)

    # Set Webhook if WEBHOOK_HOST is defined else Start polling
    webhook_status = None
    if WEBHOOK_HOST is not None:
        print("Attempting setting webhook on port:", WEBHOOK_PORT)
        webhook_status = application.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path=TOKEN,
            webhook_url="{}/{}".format(WEBHOOK_HOST, TOKEN),
        )
    if not webhook_status:
        print("webhook not configured.. Starting polling")
        application.run_polling(poll_interval=0.4, timeout=3600)
    else:
        print("webhook setup ok")


class Runner:
    def __init__(self):
        os.makedirs(TEMP_DIR, exist_ok=True)
        self.runfile = os.path.join(TEMP_DIR, "_run.tmp")

    def already_running(self):
        return os.path.exists(self.runfile)

    def set_running(self):
        open(self.runfile, "a").close()

    def stop_running(self):
        os.remove(self.runfile)


if __name__ == "__main__":
    validate()
    runner = Runner()
    if runner.already_running():
        runner.stop_running()
        print("Stopping existing instance")
    else:
        runner.set_running()
        print("Running new instance")
        processes = [
            Process(target=bot_process),
            Process(target=shell_process),
        ]
        # Start all processes
        for proc in processes:
            proc.start()
        try:
            while runner.already_running():
                time.sleep(2)
            # Terminate all processes
            for proc in processes:
                proc.terminate()
            print("Terminated via runner signal")
        except:
            # Terminate all processes
            for proc in processes:
                proc.terminate()
            runner.stop_running()
            print("Stopping existing instance")
