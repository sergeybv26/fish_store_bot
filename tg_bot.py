"""Модуль ТГ бота магазина"""

from functools import partial
import logging
import logging.config

from environs import Env
import redis
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, CommandHandler, Filters

from log.config import log_config


logger = logging.getLogger('shop_bot')

def start(bot, update):
    """Хэндлер состояния START"""
    update.message.reply_text(text='Привет!')
    return "ECHO"

def echo(bot, update):
    """Хэндлер для состояния ECHO"""
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"

def handle_users_reply(update, context, states_functions, redis_client):
    """Функция, которая запускается при любом сообщении от пользователя и решает как его обработать."""
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = redis_client.get(chat_id).decode("utf-8")

    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(context.bot, update)
        redis_client.set(chat_id, next_state)
    except Exception as err:
        print(err)

def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_pswd = env('REDIS_PASSWORD')

    logging.config.dictConfig(log_config)
    logger.warning('ТГ-бот запущен')

    redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_pswd)

    states_functions = {
        'START': start,
        'ECHO': echo
    }

    handler_kwargs = {
        'states_functions': states_functions,
        'redis_client': redis_client
    }

    handle_users_reply_partial = partial(handle_users_reply, **handler_kwargs)

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_partial))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply_partial))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_partial))
    updater.start_polling()


if __name__ == '__main__':
    main()
