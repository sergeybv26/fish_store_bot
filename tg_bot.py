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
from moltin_api import MoltinClient

from log.config import log_config


logger = logging.getLogger('shop_bot')

def create_menu_button(moltin_client):
    """Формирует inline кнопки меню с товарами"""
    products_moltin = moltin_client.get_products()
    products = [{'id': product.get('id'), 'name': product['attributes'].get('name')}
                for product in products_moltin.get('data')]
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def create_message_for_cart(chat_id, moltin_client):
    """Формирует сообщение и кнопки для отображения в корзине"""
    cart_items = moltin_client.get_cart_items(chat_id)
    cart = moltin_client.get_cart(chat_id)
    cart = cart.get('data')
    cart_items = cart_items.get('data')
    keyboard = []
    message = ''
    for cart_item in cart_items:
        message += textwrap.dedent(f'''
{cart_item.get('name')}
{cart_item.get('description')}
{cart_item['meta']['display_price']['with_tax']['unit']['formatted']} за кг
В корзине {cart_item.get('quantity')} кг на {cart_item['meta']['display_price']['with_tax']['value']['formatted']}

                                   ''')
        keyboard.append([InlineKeyboardButton(f"Убрать из корзины {cart_item['name']}",
                                              callback_data=cart_item['id'])])
    message += textwrap.dedent(f'''
Итого: {cart['meta']['display_price']['with_tax']['formatted']}
                               ''')
    keyboard.append([InlineKeyboardButton('В меню', callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return message, reply_markup

def start(bot, update, context, moltin_client):
    """Хэндлер состояния START"""
    reply_markup = create_menu_button(moltin_client)
    update.message.reply_text(text='Привет! Пожалуйста выберите товар:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, context, moltin_client):
    """Хэндлер обработки нажатия на товар"""
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'cart':
        cart_message, reply_markup = create_message_for_cart(chat_id, moltin_client)
        bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        bot.send_message(text=cart_message, chat_id=chat_id, reply_markup=reply_markup)
        return 'HANDLE_CART'
    context.user_data['product_id'] = query.data
    product = moltin_client.get_product(query.data)
    product = product.get('data')
    image_id = product['relationships']['main_image']['data']['id']
    image_link = moltin_client.get_file(image_id)
    product_details = textwrap.dedent(f'''
{product['attributes'].get('name')}
{product['meta']['display_price']['without_tax']['formatted']}
{product['attributes'].get('description')}
                                      ''')
    keyboard = [
        [InlineKeyboardButton('1 кг', callback_data=1),
         InlineKeyboardButton('5 кг', callback_data=5),
         InlineKeyboardButton('10 кг', callback_data=10),
         ],
        [InlineKeyboardButton('Корзина', callback_data='basket')],
        [InlineKeyboardButton('Назад', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
    bot.sendPhoto(chat_id=chat_id, photo=image_link, caption=product_details, reply_markup=reply_markup)

    return 'HANDLE_DESCRIPTION'

def handle_description(bot, update, context, moltin_client):
    """Хэндлер обработки кнопок в подробном отображении товара"""
    query = update.callback_query
    callback_data = query.data
    chat_id = query.message.chat_id
    product_id = context.user_data['product_id']
    if callback_data == 'back':
        reply_markup = create_menu_button(moltin_client)
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.send_message(text='Привет! Пожалуйста выберите товар:', chat_id=chat_id,
                         reply_markup=reply_markup)
        return 'HANDLE_MENU'
    elif callback_data == 'cart':
        cart_message, reply_markup = create_message_for_cart(chat_id, moltin_client)
        bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        bot.send_message(text=cart_message, chat_id=chat_id, reply_markup=reply_markup)
        return 'HANDLE_CART'
    else:
        moltin_client.add_to_basket(chat_id, product_id, int(callback_data))
        return 'HANDLE_DESCRIPTION'

def handle_cart(bot, update, context, moltin_client):
    """Хэндлер обработки корзины"""
    query = update.callback_query
    callback_data = query.data
    chat_id = query.message.chat_id
    if callback_data == 'main_menu':
        reply_markup = create_menu_button(moltin_client)
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.send_message(text='Привет! Пожалуйста выберите товар:', chat_id=chat_id,
                         reply_markup=reply_markup)
        return 'HANDLE_MENU'
    else:
        moltin_client.remove_item_from_cart(chat_id, callback_data)
        cart_message, reply_markup = create_message_for_cart(chat_id, moltin_client)
        bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        bot.send_message(text=cart_message, chat_id=chat_id, reply_markup=reply_markup)
        return 'HANDLE_CART'

def handle_users_reply(update, context, states_functions, redis_client, moltin_client):
    """Функция, которая запускается при любом сообщении от пользователя и решает как его обработать."""

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    logger.info(f'{user_reply=}')
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = redis_client.get(chat_id).decode("utf-8")

    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(context.bot, update, context, moltin_client)
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

    moltin_client = MoltinClient(moltin_client_id, moltin_client_secret)
    moltin_client.auth()

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart
    }

    handler_kwargs = {
        'states_functions': states_functions,
        'redis_client': redis_client,
        'moltin_client': moltin_client
    }

    handle_users_reply_partial = partial(handle_users_reply, **handler_kwargs)

    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_partial))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply_partial))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_partial))
    updater.start_polling()


if __name__ == '__main__':
    main()
