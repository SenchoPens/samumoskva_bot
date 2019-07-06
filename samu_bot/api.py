from functools import wraps

from requests import get, post, RequestException

from fo_bot.settings import API_TOKEN
from fo_bot.logger import logger


class APIMethodException(RequestException):
    """Represents exception during calling a method"""

    def __init__(self, message, code, text):
        super().__init__(message)
        self.code = code
        self.text = text


class APIMethod:
    _url = 'https://findtheowner.ru/api'
    def __init__(self, method, token, request_type):
        self._method = self._url + method
        self._token = token
        self._request_type = request_type

    def __call__(self, **kwargs):
        if self._request_type == 'post':
            res = post(self._method, headers={'Authorization': f'Bearer {self._token}'}, data=kwargs)
        else:
            res = get(self._method, headers={'Authorization': f'Bearer {self._token}'})

        try:  # Probably there is a better way to raise from
            res.raise_for_status()
        except RequestException as e:
            error_text = res.text.replace('\n', r'\n')
            logger.warning(f'Request error: {res.status_code}. Request URL: {res.url}. Request text: {error_text}')
            raise APIMethodException(f'Something bad with request: {res.status_code}',
                                     res.status_code, e.response) from e

        res_json = res.json()
        api_err_code = int(res_json.get('error', False))
        if api_err_code:
            raise APIMethodException(f'Request to API ended up with error status code {api_err_code}',
                                     api_err_code, res_json['message'])

        return res_json


class API:
    _api_methods = {
        'auth': ('/auth/login', 'post'),
        'register': ('/auth/register', 'post'),
        'balance': ('/user/balance', 'post'),
        'service': ('/service', 'get'),
        'recharge': ('/pay/recharge', 'post'),
        'order': ('/order', 'post'),
        'search': ('/rosreestr/search', 'post'),
        'info': ('/rosreestr/info', 'post')
    }

    def __init__(self, token):
        self._token = token

    def __getattr__(self, item):
        logger.debug('API Method call {item}')
        method, request_type = self._api_methods[item]
        return APIMethod(method=method, token=self._token, request_type=request_type)


def main():
    import pprint
    t = API(API_TOKEN)
    #t.balance(phone='+79263793151')
    pprint.pprint(t.search(search='77:01:0001054:1317'))


if __name__ == '__main__':
    main()
