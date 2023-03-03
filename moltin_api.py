"""Модуль взаимодействия с API Moltin"""
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
        self.auth_url = 'https://api.moltin.com/oauth/access_token'
        self.get_products_url = 'https://api.moltin.com/catalog/products'
        self.get_product_url = 'https://api.moltin.com/catalog/products/'
        self.get_file_url = 'https://api.moltin.com/v2/files/'

    def auth(self):
        """Авторизация на Motlin"""
        auth_payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        response_auth = requests.post(url=self.auth_url, data=auth_payload)

        response_auth.raise_for_status()
        response_auth = response_auth.json()
        self.access_token = response_auth['access_token']
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

    def get_products(self):
        """Получает продукты"""
        response = requests.get(self.get_products_url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_product(self, id):
        """Получает продукт по id"""
        response = requests.get(f'{self.get_product_url}{id}/', headers=self.headers)
        response.raise_for_status()

        return response.json()

    def get_file(self, id):
        """Получает ссылку на файл"""
        response = requests.get(f'{self.get_file_url}{id}/', headers=self.headers)
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

    def get_basket_items(self, user_id):
        """Получает товары корзины

        Args:
            user_id (str): id пользователя
        """
        response = requests.get(f'https://api.moltin.com/v2/carts/{user_id}/items', headers=self.headers)
        response.raise_for_status()

        return response.json()

if __name__ == '__main__':
    env = Env()
    env.read_env()
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')

    motlin_client = MoltinClient(moltin_client_id, moltin_client_secret)
    motlin_client.auth()

    products = motlin_client.get_products()
    pprint(products)
