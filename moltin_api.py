"""Модуль взаимодействия с API Moltin"""
import datetime
from environs import Env
import requests
from pprint import pprint


class MoltinClient():
    """Класс, реализующий взаимодействие с motlin"""
    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ''
        self.headers = {}
        self.expire_token_time = ''

    def auth(self):
        """Авторизация на Motlin"""
        auth_payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        if self.access_token and datetime.datetime.now() < self.expire_token_time:
            return

        response_auth = requests.post(url='https://api.moltin.com/oauth/access_token', data=auth_payload)

        response_auth.raise_for_status()
        response_auth = response_auth.json()
        self.expire_token_time = datetime.datetime.fromtimestamp(response_auth['expires'])
        self.access_token = response_auth['access_token']
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

    def get_products(self):
        """Получает продукты"""
        self.auth()
        response = requests.get('https://api.moltin.com/catalog/products', headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_product(self, id):
        """Получает продукт по id
        Args:
            id (str): id товара
        """
        self.auth()
        response = requests.get(f'https://api.moltin.com/catalog/products/{id}/', headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_file(self, id):
        """Получает ссылку на файл
         Args:
            id (str): id изображения
        """
        self.auth()
        response = requests.get(f'https://api.moltin.com/v2/files/{id}/', headers=self.headers)
        response.raise_for_status()
        response = response.json()

        return response['data']['link']['href']

    def add_to_basket(self, user_id, product_id, quantity):
        """Добавляет товар в корзину

        Args:
            user_id (str): id пользователя
            product_id (str): id товара
            quantity (int): количество товара
        """
        self.auth()
        payload = {
            "data": {
                "id": product_id,
                "type": "cart_item",
                "quantity": quantity
            }
        }
        response = requests.post(f'https://api.moltin.com/v2/carts/{user_id}/items/',
                                 json=payload, headers=self.headers)
        response.raise_for_status()

    def get_cart_items(self, user_id):
        """Получает товары корзины

        Args:
            user_id (str): id пользователя
        """
        self.auth()
        response = requests.get(f'https://api.moltin.com/v2/carts/{user_id}/items', headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_cart(self, user_id):
        """Получает корзину пользователя

        Args:
            user_id (str): id пользователя
        """
        self.auth()
        response = requests.get(f'https://api.moltin.com/v2/carts/{user_id}', headers=self.headers)
        response.raise_for_status()

        return response.json()

    def remove_item_from_cart(self, user_id, product_id):
        """Удаляет продукт из корзины

        Args:
            user_id (str): id пользователя
            product_id (str): id продукта
        """
        self.auth()
        response = requests.delete(f'https://api.moltin.com/v2/carts/{user_id}/items/{product_id}',
                                   headers=self.headers)
        response.raise_for_status()

    def create_customer(self, chat_id, email):
        """Создает покупателя

        Args:
            chat_id (str): id пользователя
            email (str): email пользователя
        """
        self.auth()
        payload = {
            "data": {
                "type": "customer",
                "name": chat_id,
                "email": email
            }
        }
        response = requests.post('https://api.moltin.com/v2/customers', headers=self.headers, json=payload)
        response.raise_for_status()


if __name__ == '__main__':
    env = Env()
    env.read_env()
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')

    motlin_client = MoltinClient(moltin_client_id, moltin_client_secret)
    motlin_client.auth()

    products = motlin_client.get_products()
    pprint(products)
