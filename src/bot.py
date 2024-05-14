
import asyncio
import os

from telegram.ext import Application, Updater, CommandHandler, MessageHandler, InlineQueryHandler, CallbackQueryHandler
import telegram.ext.filters as Filters
from telegram.constants import SUPPORTED_WEBHOOK_PORTS

import handlers

WEBHOOK_PORT = int(os.environ.get('PORT', 80))
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')


def validate():
    assert WEBHOOK_PORT in SUPPORTED_WEBHOOK_PORTS, f"Supported ports are f{SUPPORTED_WEBHOOK_PORTS}"

def main():
    """Start the bot."""
    
    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands(handlers.bot_commands)

    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", handlers.start, block=False))
    application.add_handler(CommandHandler("help", handlers.help, block=False))

    application.add_handler(CommandHandler("debug", handlers.debug, block=False))

    application.add_handler(CommandHandler("cache", handlers.cache_only, block=False))

    application.add_handler(CommandHandler("get", handlers.get_media, block=False))

    application.add_handler(CommandHandler("search", handlers.search, block=False))
    # application.add_handler(CallbackQueryHandler())

    # # on noncommand i.e message - get a response
    application.add_handler(MessageHandler(Filters.TEXT, handlers.generate_response, block=False))

    application.add_handler(InlineQueryHandler(handlers.inlinequery, block=False))
    
    # # log all errors
    application.add_error_handler(handlers.error)

    # Set Webhook on Heroku if WEBHOOK_HOST is defined else Start polling
    webhook_status = None
    if WEBHOOK_HOST is not None:
        print('Attempting setting webhook on port:', WEBHOOK_PORT)
        webhook_status = application.run_webhook(
        # webhook_status = updater.start_webhook(
            listen="0.0.0.0",
            port=int(WEBHOOK_PORT),
            url_path=TOKEN,
            webhook_url='{}/{}'.format(WEBHOOK_HOST, TOKEN)
        )
    if not webhook_status :
        print("webhook not configured.. Starting polling")
        application.run_polling(poll_interval=0.4, timeout=3600)
    else:
        print("webhook setup ok")
        

if __name__ == '__main__':
    validate()
    main()
