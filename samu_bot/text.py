from typing import NamedTuple


class Name(NamedTuple):
    rus: str
    eng: str

    def get_pretty(self):
        return '«' + self.rus + '»'


class ActionName:
    start = Name(rus='Начать', eng='start')
    end = Name(rus='Завершить', eng='end')
    cancel = Name(rus='Отменить', eng='cancel')
    show_help = Name(rus='Помощь', eng='help')
    add_person = Name(rus='Добавить', eng='add_person')
    search = Name(rus='Искать', eng='search')
