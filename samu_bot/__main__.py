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

from samu_bot.logger import logger
from samu_bot.settings import *
from samu_bot.api import APIMethodException
from samu_bot.text import ActionName

# Enable logging
logger.info('-' * 50)


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
    phone = update.message.contact.phone_number
    logger.info(f'User {update.effective_user.name} send a contact with phone number {phone}')
    context.user_data['phone'] = phone
    #api.auth(phone=context.user_data['phone'])
    update.message.reply_text(
        f'Вы успешно авторизовались.'
    )
    show_help(update, context)
    return MAIN


@logged_only
def show_help(update, context):
    update.message.reply_text(
        f'Добавить информацию по бездомному: {ActionName.add_person.get_pretty()}'
        f'\nИскать бездомного в базе данных: {ActionName.search.get_pretty()}'
        f'\nВывести эту справку: {ActionName.show_help.get_pretty()}'
        f'\n\nЧтобы добавить информацию о контакте с бездомным, сначала найдите бездомного в базе данных.'
    )
    return


@logged_only
def add_person(update, context):
    #link = api.add_person()
    link = 'https://duckduckgo.com/?q=Член'
    update.message.reply_text(
        f'Чтобы добавить бенефициара, перейдите по этой ссылке: {link}'
    )
    return


@logged_only
def ask_name_to_search(update, context):
    update.message.reply_text(
        'Напишите мне фамилию и/или имя бенефициара.'
    )
    return SEARCH_RESULT


def search(update, context):
    name = update.message.text
    #persons = api.search(name)
    persons = [('Батый Мангыр', 1)]
    for person in persons:
        update.effective_message.reply_text(
            f'ФИО: {person[0]}',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    text='Подробнее',
                    callback_data=f'{CallbackPrefix.VIEW_INFO}{person[1]}'
                )]]
            )
        )
    return MAIN


@remove_prefix
def view_info(update, context):
    pid = update.callback_query.data
    #info = api.view_info(pid)
    info = 'Разработчик, закончил финяшку'
    update.effective_message.reply_text(
        info,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                text='Добавить контакт',
                callback_data=f'{CallbackPrefix.ADD_CONTACT}{pid}'
            )]]
        )
    )
    return


def request_location(update, context):
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


def add_contact(update, context):
    location = update.message.location
    update.message.reply_text(
        f'Координаты: {(location.latitude, location.longitude)}'
    )
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


def cancel(update, context):
    return MAIN


def end(update, context):
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
                make_handler(add_person, ActionName.add_person),
                make_handler(ask_name_to_search, ActionName.search),
                CallbackQueryHandler(view_info, pattern=f'^{CallbackPrefix.VIEW_INFO}\d+$'),
                CallbackQueryHandler(request_location, pattern=f'^{CallbackPrefix.ADD_CONTACT}\d+$'),
            ],
            SEARCH_RESULT: [
                MessageHandler(Filters.text, search),
            ],
            CONTACT_LOCATION_RESULT: [
                MessageHandler(Filters.location, add_contact),
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

    if 'debug-start' in sys.argv:
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
