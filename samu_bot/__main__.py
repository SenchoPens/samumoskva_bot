# -*- coding: utf-8 -*-

import re
import sys

from functools import wraps

from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    PicklePersistence,
)
from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
import requests

from samu_bot.logger import logger
from samu_bot.settings import *
from samu_bot.api import APIMethodException
from samu_bot.text import ActionName

# Enable logging
logger.info('-' * 50)


class ObjectId:
    def __init__(self, _):
        pass


command_markup = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in ('Добавить', 'Искать', 'Помощь')])


def remove_prefix(f):
    @wraps(f)
    def wrapper(update, context):
        update.callback_query.data = update.callback_query.data[1:]
        return f(update, context)
    return wrapper


def logged_only(f):
    @wraps(f)
    def wrap(update, context):
        if context.user_data['phone']:
            return f(update, context)
    return wrap


def format_for_get(*args):
    return {'data': '{' + ', '.join(f'{key}: {value}' for key, value in args) + '}'}


def dict_to_telegram_text(d):
    return '\n'.join(f'*{key}*: {value}' for key, value in d.items())


def start(update, context):
    user = update.effective_user
    context.user_data['phone'] = ''
    logger.info(f'User {user.name} started the conversation.')

    contact_button = KeyboardButton(text="Отправить мне контакт", request_contact=True)
    update.message.reply_text(
        f'Здравствуйте, {user.first_name}.\n'
        'Поделитесь со мной своим номером телефона - это необходимо для авторизации',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[contact_button]],
            one_time_keyboard=True
        )
    )
    return MAIN


def auth(update, context):
    phone = update.message.contact.phone_number.replace('+7', '8')
    if phone.startswith('7'):
        phone = '8' + phone[1:]
    logger.info(f'User {update.effective_user.name} send a contact with phone number {phone}')
    try:
        res = requests.get(f'{API_URL}/api/staff/check/', params=format_for_get(('"phone"', f'"{phone}"')))
        res.raise_for_status()
    except requests.RequestException as e:
        logger.info(f'Request error on search: {e}')
        update.effective_message.reply_text(
            'Что-то не так с сервером. Пожалуйста, повторите авторизвацию позже.'
        )
        return END
    logger.info(res.text, res.url)
    if res.text == 'True':
        context.user_data['phone'] = phone
        update.message.reply_text(
            f'Вы успешно авторизовались.',
            reply_markup=command_markup,
        )
        show_help(update, context)
    else:
        update.message.reply_text(
            'Ваш номер телефона отсутствует в системе.'
        )
        return END
    return MAIN


@logged_only
def show_help(update, context):
    update.message.reply_text(
        f'Добавить информацию по бездомному: {ActionName.add_person.get_pretty()}'
        f'\nИскать бездомного в базе данных: {ActionName.search.get_pretty()}'
        f'\nВывести эту справку: {ActionName.show_help.get_pretty()}'
        f'\n\nЧтобы добавить информацию о контакте с бездомным, сначала найдите бездомного в базе данных.',
        reply_markup=command_markup,
    )
    return


@logged_only
def ask_name_to_search(update, context):
    update.message.reply_text(
        'Напишите мне фамилию и имя бенефициара.'
    )
    return SEARCH_RESULT


def search(update, context):
    cred = update.message.text.split()
    if len(cred) not in range(1, 4):
        update.effective_message.reply_text(
            'Вам нужно ввести фамилию и имя бенефициара.'
        )
        return MAIN
    data = zip(('"Фамилия"', '"Имя"', '"Отчество"'), (f'"{x}"' for x in cred))

    try:
        res = requests.get(
            f'{API_URL}/api/beneficiary/info/',
            params=format_for_get(*data)
        )
        res.raise_for_status()
    except requests.RequestException as e:
        logger.info(f'Request error on search: {e}')
        update.effective_message.reply_text(
            'Что-то не так с сервером. Пожалуйста, повторите поиск позже.'
        )
        return MAIN

    try:
        #res_json = json.loads(('[{' + txt[txt.find(',') + 1:]).replace("'", '"'))
        logger.info(res.text)
        persons = eval(res.text)
    except SyntaxError as e:
        logger.info(f'Eval error on search: {e}')
        update.effective_message.reply_text(
            'Произошла какая-то ошибка. Пожалуйста, повторите поиск позже.'
        )
        return MAIN

    for person in persons:
        send_info_about_person(update, context, person=person)
    if not persons:
        update.effective_message.reply_text(
            'Ваш запрос не дал никаких результатов.'
        )
    return MAIN


def send_info_about_person(update, context, *, person):
    person.pop('_id')
    pid = person.pop('id')
    contacts = person.pop('Посещения')
    update.effective_message.reply_text(
        dict_to_telegram_text(person),
        parse_mode='markdown',
    )
    """
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                text=f'{i}',
                callback_data=f'{CallbackPrefix.VIEW_INFO}{person[1]}'
            )] for i in range(len(contacts))]
        ),
    )
    """
    update.effective_message.reply_text(
        'Посещения:'
    )
    for contact in contacts:
        update.effective_message.reply_text(
            dict_to_telegram_text(contact),
            parse_mode='markdown'
        )
    update.effective_message.reply_text(
        f'Всего посещений: {len(contacts)}',
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                text='Добавить контакт',
                callback_data=f'{CallbackPrefix.ADD_CONTACT}{pid}'
            )]]
        )
    )
    return MAIN


@remove_prefix
def view_info(update, context):
    return


@remove_prefix
def request_location_for_contact(update, context):
    context.user_data['pid'] = update.callback_query.data
    context.user_data['chosen'] = add_contact
    update.effective_message.reply_text(
        'Чтобы добавить информацию о контакте, перешлите мне свою локацию, '
        'или нажмите сюда: /cancel (отменить операцию)',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(
                text='Отправить локацию',
                request_location=True,
            )]]
        )
    )
    return CONTACT_LOCATION_RESULT


def request_location_for_person(update, context):
    context.user_data['chosen'] = add_person
    update.effective_message.reply_text(
        'Чтобы добавить информацию о бенефициаре, перешлите мне свою локацию',
        reply_markup=ReplyKeyboardMarkup(
            [
             [KeyboardButton(
                text='Отправить локацию',
                request_location=True,
            )],
             [KeyboardButton(
                 text='Отменить'
             )],
            ]
        )
    )
    return CONTACT_LOCATION_RESULT


def accept_location(update, context):
    location = update.message.location
    lat, long = location.latitude, location.longitude
    user = update.effective_user
    surname, name = user.last_name, user.first_name
    return context.user_data['chosen'](update, context, params=f'?coordinates={lat}+{long}&staff={surname}+{name}')


def add_person(update, context, *, params):
    link = f'{API_URL}/addbeneficiary{params}'
    update.message.reply_text(
        f'Чтобы добавить бенефициара, нажмите на эту кнопку, чтобы перейти на сайт и заполнить анкету:',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text='Заполнить анкету', url=link)
        ]])
    )
    show_help(update, context)
    return MAIN


def add_contact(update, context, *, params):
    pid = context.user_data['pid']
    link = f'{API_URL}/{pid}/regular_check/{params}'
    update.message.reply_text(
        'Чтобы добавить контакт на сайте, нажмите на эту кнопку:',
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='Добавить контакт', url=link)]]
        )
    )
    show_help(update, context)
    return MAIN


def handle_error(update, context):
    """ Error handler """
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    try:
        raise context.error
    except APIMethodException as e:
        if e.code in range(400, 500):  # client error
            err = e.text
            update.effective_message.reply_text(e.text)
        else:
            err = 'Something bad'
            update.effective_message.reply_text('Извините, произошла какая-то ошибка. Попробуйте позже.')
        logger.warning(f'API error: "{err}" with api request by {update.effective_user.name}')
    return MAIN


def cancel(update, context):
    logger.info('User canceled')
    return MAIN


def end(update, context):
    logger.info('User ended conversation')
    return END


########################################################################################################################
def make_handler(callback, name):
    russian_handler = MessageHandler(Filters.regex(re.compile('^' + name.rus, flags=re.IGNORECASE)), callback)
    return russian_handler


def main():
    pp = PicklePersistence(filename='samu_persistance.persistance')

    if 'proxy' in sys.argv:
        logger.info(f'Starting in PROXY mode. Proxy URL: {REQUEST_KWARGS["proxy_url"]}')
        request_kwargs=REQUEST_KWARGS
    else:
        logger.info('Starting in NORMAL mode')
        request_kwargs = None

    updater = Updater(
        token=BOT_TOKEN,
        request_kwargs=request_kwargs,
        persistence=pp,
        use_context=True,
    )

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states={
            MAIN: [
                MessageHandler(Filters.contact, auth),
                make_handler(request_location_for_person, ActionName.add_person),
                make_handler(ask_name_to_search, ActionName.search),
                CallbackQueryHandler(view_info, pattern=f'^{CallbackPrefix.VIEW_INFO}\d+$'),
                CallbackQueryHandler(request_location_for_contact, pattern=f'^{CallbackPrefix.ADD_CONTACT}\d+$'),
            ],
            SEARCH_RESULT: [
                MessageHandler(Filters.text, search),
            ],
            CONTACT_LOCATION_RESULT: [
                MessageHandler(Filters.location, accept_location),
            ],
        },
        fallbacks=[
            make_handler(cancel, ActionName.cancel),
            make_handler(show_help, ActionName.show_help),
            make_handler(end, ActionName.end),
        ],
        name='samu_conversation',
        persistent=True,
    )
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(handle_error)

    #if 'debug-start' in sys.argv:
    if True:
        conv_handler.conversations[(182705944, 182705944)] = None
        dp.user_data[182705944] = {}

    logger.info('Starting the bot...')
    # Start the Bot
    updater.start_polling()

    updater.idle()

    logger.info('The bot has stopped.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.warning(f'A fatal error occured: {e}')
        raise e
