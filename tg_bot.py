"""Модуль ТГ бота магазина"""

from functools import partial
import logging
import logging.config
import textwrap
from pprint import pprint
from environs import Env
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, CommandHandler, Filters
from moltin_api import MotlinClient

from log.config import log_config


logger = logging.getLogger('shop_bot')

def start(bot, update, motlin_client):
    """Хэндлер состояния START"""
    products_motlin = motlin_client.get_products()
    products = [{'id': product.get('id'), 'name': product['attributes'].get('name')}
                for product in products_motlin.get('data')]
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Привет! Пожалуйста выберите товар:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, motlin_client):
    """Хэндлер обработки нажатия на товар"""
    query = update.callback_query
    product = motlin_client.get_product(query.data)
    product = product.get('data')
    image_id = product['relationships']['main_image']['data']['id']
    image_link = motlin_client.get_file(image_id)
    product_details = textwrap.dedent(f'''
{product['attributes'].get('name')}
{product['meta']['display_price']['without_tax']['formatted']}
{product['attributes'].get('description')}
                                      ''')
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    bot.sendPhoto(chat_id=query.message.chat_id, photo=image_link, caption=product_details)

    return 'START'

def handle_users_reply(update, context, states_functions, redis_client, motlin_client):
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
        next_state = state_handler(context.bot, update, motlin_client)
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
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')

    logging.config.dictConfig(log_config)
    logger.info('ТГ-бот запущен')

    redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_pswd)

    motlin_client = MotlinClient(moltin_client_id, moltin_client_secret)
    motlin_client.auth()

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu
    }

    handler_kwargs = {
        'states_functions': states_functions,
        'redis_client': redis_client,
        'motlin_client': motlin_client
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
