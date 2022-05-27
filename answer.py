from typing import Union

from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message, CallbackQuery

# from okmakbot import Step


class Answer:

    @classmethod
    async def get_answer_type(cls, request: Union[Message, CallbackQuery]):
        answer_type = None
        if isinstance(request, Message):
            answer_type = request.answer
        elif isinstance(request, CallbackQuery):
            answer_type = request.message.edit_text
        return answer_type

    @classmethod
    async def get_markup_btns(cls, items_list, prefix='') -> list:
        markup_btns = list()
        for item in sorted(items_list):
            btn_item = InlineKeyboardButton(text=prefix + item, callback_data=item)
            markup_btns.append(btn_item)
        return markup_btns

    # @classmethod
    # async def get_answer_text(cls, current_list: list, state: FSMContext, updated_time: str = str()) -> str:
    #     txt = str()
    #     current_state = await state.get_state()
    #     if current_state == Step.wait_add_to_list.state:
    #         if current_list:
    #             txt = 'Что нужно добавить? \U0001F914 '
    #         else:
    #             txt = 'Выбирать не из чего... \U00002639'
    #     if current_state == Step.wait_del_from_list.state:
    #         if current_list[0]:
    #             txt = f'Вот тебе список! \U0001F609 \n'
    #             txt += f'Ред. в {updated_time}'
    #         else:
    #             txt = 'Да вроде бы всё есть! \U0001F389 '
    #     if current_state == Step.wait_del_forever.state:
    #         if current_list[0]:
    #             txt = 'Что можно удалить? \U0001F914 '
    #         else:
    #             txt = 'Удалять нечего! \U0001F923'
    #     return txt
