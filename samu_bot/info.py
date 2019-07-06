from typing import NamedTuple
import datetime

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
    ReplyKeyboardMarkup,
    KeyboardButton,
)


class Question(NamedTuple):
    qid: int
    text: str
    qtype: str


def get_questions():
    return []


def add_info(update, context):
    questions = get_questions()

    user = update.effective_user
    date = datetime.date.today()
    context.user_data['pending_info'] = {
        'Имя сотрудника': f'{user.last_name} {user.first_name}',
        'Дата': f'{date.today}:{date.month}:{date.year}',
