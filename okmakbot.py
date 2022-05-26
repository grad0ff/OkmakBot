import logging
import sys
from typing import Union
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, \
    InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils import executor

import config
from db_manage import BaseList, Blocked

if sys.platform != 'win32':
    logging.basicConfig(filename=config.LOG_FILE, filemode='w')

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

shopping_list = BaseList('product')
task_list = BaseList('task')
blocked_list = Blocked()
db_table = shopping_list

users = list(config.users.values())
rows_count = 2

btn_shopping = KeyboardButton('Покупки')
btn_tasks = KeyboardButton('Дела')
btn_add = KeyboardButton('Внести в список')
btn_show = KeyboardButton('Показать список')
btn_all = KeyboardButton('Показать всё')
btn_back = KeyboardButton('Выйти из')
# btn_new_record = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_record')

btn_yes = InlineKeyboardButton('Да', callback_data='YES')
btn_no = InlineKeyboardButton('Нет', callback_data='NO')

menu_btns_txt = [btn_shopping.text, btn_tasks.text]
submenu_btn_txt = [btn_add.text, btn_show.text, btn_all.text, btn_back.text]
yn_btns_data = [btn_yes.callback_data, btn_no.callback_data]


# priority_btns_txts = [btn_priority_1.text, btn_priority_2.text]


class Step(StatesGroup):
    wait_current_list = State()
    wait_action = State()
    wait_add_to_list = State()
    wait_priority = State()
    wait_del_from_list = State()
    wait_del_forever = State()
    wait_new_item = State()

    submenu_states = [wait_add_to_list, wait_priority, wait_del_from_list, wait_del_forever]


async def filter_users(message: Message):
    """
    Фильтрует пользователей и возвращает сообщение если пользователь в списке зарегистрированных, иначе вносит в БД в
    таблицу незарегистрированных пользователей
    """
    user_id = message.from_user.id
    if user_id not in users:
        blocked_list.add(user_id, message.text)
    else:
        return message


@dp.message_handler(filter_users, commands='start', state='*')
@dp.message_handler(Text(startswith=btn_back.text), state='*')
async def start_chat(message: Message, state: FSMContext):
    """
    Запускает бота и отображает основное меню
    """
    global db_table
    db_table = None
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(btn_shopping)
    markup.add(btn_tasks)
    await message.answer(f'Всегда готов! \U0001F44D \n'
                         'Выбери нужный раздел \U0001F4C2', reply_markup=markup)
    await state.finish()
    await Step.wait_current_list.set()


@dp.message_handler(commands='cancel', state='*')
async def cancel(message: Message, state: FSMContext):
    """
    Завершает чат и сбрасывает машину состояний
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Чат завершен!  \U000026D4", reply_markup=ReplyKeyboardRemove())


# @dp.message_handler(lambda message: message.text in menu_btns_txt, state=[Step.wait_current_list])
@dp.message_handler(Text(equals=menu_btns_txt), state=[Step.wait_current_list])
async def selected_current_list(message: Message, state: FSMContext):
    """
    Отображает пункты разделов, адаптирует текст кнопки выхода из раздела в соответствии с выбранным разделом
    """
    global db_table, rows_count
    msg_txt = message.text
    await state.update_data(current_list=msg_txt)
    if msg_txt == btn_shopping.text:
        db_table = shopping_list
        btn_back.text = 'Выйти из Покупок'
        rows_count = 2
    elif msg_txt == btn_tasks.text:
        db_table = task_list
        btn_back.text = 'Выйти из Дел'
        rows_count = 1
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_add, btn_show)
    markup.add(btn_all, btn_back)
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)
    await Step.wait_action.set()


@dp.callback_query_handler(state=[*Step.submenu_states])
@dp.message_handler(Text(equals=submenu_btn_txt), state=[Step.wait_action, *Step.submenu_states])
async def selected_action(message: Union[Message, CallbackQuery], state: FSMContext):
    """
    Отображает перечень действий, доступных для текущего списка
    """
    msg_txt = str()
    send_answer = None
    if isinstance(message, CallbackQuery):
        send_answer = message.message.edit_text
    elif isinstance(message, Message):
        send_answer = message.answer
        msg_txt = message.text
        await state.update_data(action=msg_txt)
    # items_list = []
    # msg = ''

    if msg_txt == btn_show.text:
        priority_1_items, priority_2_items = db_table.actual_items
        if priority_1_items:
            msg = f'Это нужно в первую очередь! \U0001F609 \n'
            markup = await get_mrkp(priority_1_items)
            await send_answer(msg, reply_markup=markup)
        # else:
        #     msg = f'Ничего такого срочного! \U0001F609 \n'
        #     await message.answer(msg)
        if priority_2_items:
            msg = f'Это уже по возможности... \U0001F609 \n'
            markup = await get_mrkp(priority_2_items)
            await send_answer(msg, reply_markup=markup)
        # else:
        #     msg = f'Ничего такого срочного! \U0001F609 \n'
        if priority_1_items or priority_2_items:
            await send_answer(f'Ред. в {db_table.updated_time}')
        else:
            await send_answer('Да вроде бы всё есть! \U0001F389 ')
        return await Step.wait_del_from_list.set()

    if msg_txt == btn_add.text:
        items_lists = db_table.irrelevant_items
        if items_lists:
            msg = 'Что нужно добавить? \U0001F914 '
            markup = await get_mrkp(items_lists)
            await send_answer(msg, reply_markup=markup)
        else:
            await send_answer('Выбирать не из чего... \U00002639')
        return await Step.wait_add_to_list.set()

    if msg_txt == btn_all.text:
        items_list = db_table.all_items
        if items_list:
            msg = 'Что можно удалить? \U0001F914 '
            markup = await get_mrkp(items_list, prefix='\U0000274C  ')
            await send_answer(msg, reply_markup=markup)
        else:
            await send_answer('Удалять нечего! \U0001F923')
        await Step.wait_del_forever.set()
    # markup = get_mrkp(items_list)
    # await message.answer(msg, reply_markup=markup)


# @dp.callback_query_handler(Text(equals=btn_yes.callback_data), state=Step.wait_new_item)
# @dp.callback_query_handler(lambda call: call.data != btn_new_record.callback_data, state=Step.wait_add_to_list)
@dp.callback_query_handler(state=Step.wait_add_to_list)
async def add_to_list(call: CallbackQuery, state: FSMContext):
    """
    Фоновая обработка добавления записи из неактуального списка в актуальный, включая изменение статуса в БД
    """
    current_state = await state.get_state()
    # if current_state == Step.wait_new_item.state:
    #     item = (await state.get_data()).get('new_item')
    #     db_table.insert_new_item(item)
    # else:
    item = call.data
    await state.update_data(item=item)
    markup = InlineKeyboardMarkup()
    markup.add(btn_yes, btn_no)
    await call.message.edit_text('Это вот сейчас нужно вот, да? \U0001F914', reply_markup=markup)
    await Step.wait_priority.set()


# @dp.callback_query_handler(Text(equals=btn_new_record.callback_data), state=Step.wait_add_to_list)
# async def add_new_record(call: CallbackQuery):
#     """
#     Фоновая обработка кнопки  новой записи
#     """
#     await call.message.edit_text('Просто напиши тут... \U0001F447')
#     await call.answer()


@dp.callback_query_handler(state=Step.wait_priority)
async def get_priority(call: CallbackQuery, state: FSMContext):
    priority = 1 if call.data == btn_yes.callback_data else 2
    item = (await state.get_data()).get('item')
    await call.answer(f'Нужно:  {item} \U0001F44C')
    db_table.set_actual(item=item, priority=priority)
    # irrelevant_items_lists = db_table.irrelevant_items
    await Step.wait_add_to_list.set()
    # await answer_manager(call, irrelevant_items_lists, state)
    msg_obj = (await state.get_data()).get('action_obj')
    await selected_action(msg_obj, state)


@dp.callback_query_handler(state=Step.wait_del_from_list)
async def show_list(call: CallbackQuery, state: FSMContext):
    """
    Фоновая обработка переноса записи из актуального списка в неактуальный, включая изменение статуса в БД
    """
    item = call.data
    db_table.set_irrelevant(item=item)
    await call.answer(f'Уже не нужно:  {item} \U0001F44C', cache_time=1)
    await selected_action(call, state)


@dp.callback_query_handler(state=Step.wait_del_forever)
async def delete_forever(call: CallbackQuery, state: FSMContext):
    """
    Фоновая обработка удаления записи из полного списка и БД
    """
    item = call.data
    db_table.delete_item(item)
    await call.answer(f'Удалено из записей: {item} \U0001F44C', cache_time=2)
    # all_items_lists = db_table.all_items
    # await answer_manager(call, all_items_lists, state)
    msg_obj = (await state.get_data()).get('action_obj')
    await selected_action(msg_obj, state)


# async def answer_manager(call: CallbackQuery, item_lists: list, state: FSMContext):
#     """
#     Менеджер запросов, обрабатывает типы Message и CallbackQuery
#     """
#     current_state = await state.get_state()
#     answer_txt = await get_answer_txt(item_lists, current_state)
#     markup = await get_markup(item_lists, current_state)
#     await call.message.edit_text(text=answer_txt, reply_markup=markup)
#
#
# async def get_answer_txt(item_lists, current_state: str) -> str:
#     """
#     Возвращает текст сообщения, зависимости от состояния FSM и наличия данных в текущем списке
#     """
#
#     current_list = list().append(lst for lst in item_lists)
#     # if current_state == Step.wait_add_to_list.state:
#     # # сообщения для списка неактуальных записей
#
#     if current_state == Step.wait_del_from_list.state:
#         # сообщения для списка актуальных записей
#         if current_list:
#             return 'Вот список! \U0001F609 \n' f'Ред. в {db_table.updated_time}'
#         return 'Список пуст! \U0001F389 '
#     if current_state == Step.wait_del_forever.state:
#         # сообщения для списка всех записей
#         if current_list:
#             return 'Что нужно удалить? \U0001F914 '
#         return 'Удалять нечего! \U0001F923'


async def get_mrkp(items_list: list, prefix='') -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for item in sorted(items_list):
        btn_item = InlineKeyboardButton(text=prefix + item, callback_data=item)
        markup.add(btn_item)
    return markup


# async def get_markup(lists: list, current_state: str):
#     """
#     Возвращает разметку кнопок в зависимости от состояния FSM и наличия данных в текущем списке
#     """
#     global rows_count
#     markup = InlineKeyboardMarkup(row_width=rows_count)
#     mark = True
#     for lst in lists:
#         if lst:
#             btn_list = []
#             long_txt_flag = False
#             for item in sorted(lst):
#                 txt_size = sys.getsizeof(item)
#                 if txt_size > 100:
#                     long_txt_flag = True
#                 button_item = InlineKeyboardButton(item, callback_data=item)
#                 if current_state == Step.wait_add_to_list.state:
#                     if mark:
#                         button_item.text = '\U00002757' + button_item.text
#                     mark = False
#                 elif current_state == Step.wait_del_forever.state:
#                     button_item.text = '\U0000274C  ' + button_item.text
#                 btn_list.append(button_item)
#             if long_txt_flag:
#                 rows_count = 1
#             else:
#                 rows_count = 2
#             markup.row_width = rows_count
#             markup.add(*btn_list)
#     # if current_state == Step.wait_add_to_list.state:
#     #     markup.add(btn_new_record)
#
#     return markup


@dp.message_handler(filter_users, commands='blocked')
async def show_blocked(message: Message):
    markup = InlineKeyboardMarkup()
    clear_btn = InlineKeyboardMarkup(text='Очистить список', callback_data='clear_blocked')
    markup.add(clear_btn)
    msg = ''
    for item in blocked_list.blocked:
        msg += f'id: {item[0]}  datetime: {item[1]}  message: {item[2]}\n'
    await message.answer(msg, reply_markup=markup)


@dp.callback_query_handler(Text(equals='clear_blocked'))
async def clear_blocked_list(call: CallbackQuery):
    blocked_list.clear()
    await call.answer(f'Список очищен! \U0001F44C', cache_time=2)
    await call.message.delete()


# Фоновая обработка текста новой записи
@dp.message_handler(filter_users, state='*')
async def adding_new_item(message: Message, state: FSMContext):
    global db_table
    msg_txt = message.text
    if await state.get_state() == Step.wait_current_list.state:
        return await message.answer('Сначала выбери нужный раздел! \U0001F4C2')
    if msg_txt in db_table.all_items:
        return await message.answer('Не повторяйся! \U0000261D')
    if sys.getsizeof(msg_txt) > 128:
        return await message.answer('Слишком много слов! \n'
                                    'Давай покороче... \U0001F612')
    else:
        await state.update_data(item=msg_txt)
        db_table.insert_new_item(msg_txt)
        markup = InlineKeyboardMarkup()
        markup.add(btn_yes, btn_no)
        await message.answer('Это прям срочно вот, да??? \U0001F914', reply_markup=markup)
        await Step.wait_priority.set()

        # await message.answer(f'Добавить \" {msg_txt} \" в список?', reply_markup=markup)
        # await Step.wait_new_item.set()


# @dp.callback_query_handler(Text(equals=btn_no.callback_data), state=Step.wait_new_item)
# async def add_new_item(call: CallbackQuery):
#     await call.message.edit_text('Ну и ладно...')
#     await Step.wait_action.set()


if __name__ == '__main__':
    executor.start_polling(dp)

