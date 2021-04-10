
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler

import handlers

WEBHOOK_PORT = int(os.environ.get('PORT', 80))
TOKEN = os.environ.get('BOT_TOKEN')
APP_NAME = os.environ.get('HEROKU_APP_NAME')


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Sets the supported bot commands for the public
    updater.bot.set_my_commands(handlers.bot_commands)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", handlers.start, run_async=True))
    dp.add_handler(CommandHandler("help", handlers.help, run_async=True))

    dp.add_handler(CommandHandler("debug", handlers.debug, run_async=True))

    dp.add_handler(CommandHandler("download", handlers.download_only, run_async=True))

    dp.add_handler(CommandHandler("get", handlers.get_media, run_async=True))

    dp.add_handler(CommandHandler("search", handlers.search, run_async=True))

    # on noncommand i.e message - get a response
    dp.add_handler(MessageHandler(Filters.text, handlers.generate_response, run_async=True))

    dp.add_handler(InlineQueryHandler(handlers.inlinequery, run_async=True))
    
    # log all errors
    dp.add_error_handler(handlers.error)


    # Set Webhook on Heroku if APP_NAME is defined else Start polling
    try:
        if APP_NAME is None:
            raise Exception('App Name not set')
        print('Setting webhook on port:', WEBHOOK_PORT)
        webhook_status = updater.start_webhook(
            listen="0.0.0.0",
            port=int(WEBHOOK_PORT),
            url_path=TOKEN,
            webhook_url='https://{}.herokuapp.com/{}'.format(APP_NAME, TOKEN))
        if not webhook_status :
            raise Exception('Webhook status is false')
        print("webhook setup ok")
    except Exception as error:
        print("webhook setup failed:", error)
        updater.start_polling(poll_interval=0.4, timeout=3600)
        print("Started polling")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()