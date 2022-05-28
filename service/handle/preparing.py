from aiogram.types import InlineKeyboardButton


class Preparing:

    @staticmethod
    async def get_markup_btns(items_list: list, prefix='') -> list:
        if not items_list:
            return list()
        markup_btns = list()
        for item in sorted(items_list):
            btn_item = InlineKeyboardButton(text=prefix + '  ' + item, callback_data=item)
            markup_btns.append(btn_item)
        return markup_btns

    @staticmethod
    async def get_txt_for_irrelevant(items) -> str:
        if items:
            return 'Что нужно добавить?  \U0001F914 '
        return 'Выбирать не из чего...  \U0001F615'

    @staticmethod
    async def get_txt_for_actual(items: list, updated_time: str) -> str:
        for item in items:
            if item:
                return f'Вот тебе список!  \U0001F609 \n' \
                       f'Ред. в {updated_time}'
        return 'Список пуст!  \U0001F389 '

    @staticmethod
    async def get_txt_for_all(items: list) -> str:
        if items:
            return 'Что можно удалить?  \U0001F914 '
        return 'Удалять нечего!  \U0001F923'
