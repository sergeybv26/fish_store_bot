"""Модуль взаимодействия с API Moltin"""
from environs import Env
import requests
from pprint import pprint


class MotlinClient():
    """Класс, реализующий взаимодействие с motlin"""
    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ''
        self.auth_url = 'https://api.moltin.com/oauth/access_token'
        self.get_products_url = 'https://api.moltin.com/catalog/products'
        self.get_product_url = 'https://api.moltin.com/catalog/products/'

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

    def get_products(self):
        """Получает продукты"""
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(self.get_products_url, headers=headers)
        response.raise_for_status()

        return response.json()

    def get_product(self, id):
        """Получает продукт по id"""
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(f'{self.get_product_url}{id}/', headers=headers)
        response.raise_for_status()

        return response.json()


if __name__ == '__main__':
    env = Env()
    env.read_env()
    moltin_client_id = env('MOLTIN_CLIENT_ID')
    moltin_client_secret = env('MOLTIN_CLIENT_SECRET')

    motlin_client = MotlinClient(moltin_client_id, moltin_client_secret)
    motlin_client.auth()

    products = motlin_client.get_products()
    pprint(products)
