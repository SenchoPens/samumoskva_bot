import os

from enum import IntEnum, auto


# Telegram API
BOT_TOKEN = os.environ['BOT_TOKEN']
MAX_DATA_LEN = 64

END, MAIN, SEARCH_RESULT, CONTACT_LOCATION_RESULT = range(-1, 3)


class CallbackPrefix(IntEnum):
    VIEW_INFO = auto()
    ADD_CONTACT = auto()


API_TOKEN = os.environ['API_TOKEN']
API_URL = os.environ['API_URL']

REQUEST_KWARGS = {
    # socks5://address:port
    'proxy_url': os.environ.get('PROXY_URL', None),
    'urllib3_proxy_kwargs': {
        'username': os.environ.get('PROXY_USERNAME', None),
        'password': os.environ.get('PROXY_PASSWORD', None),
    }
}
