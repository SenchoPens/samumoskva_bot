import os

from enum import IntEnum, auto


# Telegram API
BOT_TOKEN = os.environ['BOT_TOKEN']
MAX_DATA_LEN = 64

END, MAIN = range(-1, 2)

WORKERS_PHONES = os.environ['WORKERS_PHONES'].split(':')

class CallbackPrefix(IntEnum):
    VIEW_INFO = auto()

API_TOKEN = os.environ['API_TOKEN']

REQUEST_KWARGS = {
    # socks5://address:port
    'proxy_url': os.environ.get('PROXY_URL', None),
    'urllib3_proxy_kwargs': {
        'username': os.environ.get('PROXY_USERNAME', None),
        'password': os.environ.get('PROXY_PASSWORD', None),
    }
}
