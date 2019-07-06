from functools import wraps


def remove_prefix(f):
    """
    A decorator around callbacks that handle CallbackButton's clicks with cad number in callback data.
    It removes callback type (prefix) from callback data.
    """
    @wraps(f)
    def wrapper(update, context):
        update.callback_query.data = update.callback_query.data[1:]
        return f(update, context)
    return wrapper


def callbackquery_message_to_message(f):
    @wraps(f)
    def wrap(update, context):
        update.message = update.callback_query.message
        return f(update, context)
    return wrap
