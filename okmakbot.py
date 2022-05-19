import asyncio
import logging
import sys

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

import config
from db_manage import Shopping, ToDo, Blocked

logging.basicConfig(filename=config.LOG_FILE, filemode='w')

storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

users = list(config.users.values())

shopping_list = Shopping()
todo_list = ToDo()
current_table = shopping_list
blocked_list = Blocked()

button_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')
rows_count = 2


async def filter_users(message: types.Message):
    """
    Фильтрует пользователей и возвращает сообщение если пользователь в списке зарегистрированных, иначе вносит в БД в
    таблицу незарегистрированных пользователей
    """
    user_id = message.from_user.id
    if user_id not in users:
        blocked_list.add(user_id, message.text)
    else:
        return message


@dp.message_handler(filter_users, commands='start')
@dp.message_handler(Text(startswith='Выход из'))
async def start_chat(message: types.Message):
    """
    Запускает бота и отображает основное меню
    """
    global current_table
    current_table = None
    await message.answer(f'Всегда готов! \U0001F44D \n')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(KeyboardButton('Покупки'))
    markup.add(KeyboardButton('Дела'))
    await message.answer(f'Выбери нужный раздел \U0001F4C2', reply_markup=markup)

    await asyncio.sleep(config.timer)
    current_table = None
    await message.answer(f'Я спать... \U0001F634', reply_markup=markup, disable_notification=True)


@dp.message_handler(Text(equals=['Покупки', 'Дела']))
async def select_table(message: types.Message):
    """
    Отображает пункты разделов, адаптирует текст кнопки выхода из раздела в соответствии с выбранным разделом
    """
    global current_table, rows_count
    back_btn_txt = ''
    if message.text == 'Покупки':
        current_table = shopping_list
        back_btn_txt = 'Покупок'
        rows_count = 2
    elif message.text == 'Дела':
        current_table = todo_list
        back_btn_txt = 'Дел'
        rows_count = 1
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('Внести в список'), KeyboardButton('Показать список'))
    markup.add(KeyboardButton('Показать всё'), KeyboardButton(f'Выход из {back_btn_txt}'))
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)


@dp.message_handler(Text(equals=['Внести в список', 'Показать список', 'Показать всё']))
async def add_to_list(message: types.Message):
    current_list = []
    mark = ''
    if message.text == 'Внести в список':
        current_list = current_table.irrelevant_items
        mark = 'ATL'
    elif message.text == 'Показать список':
        current_list = current_table.actual_items
        mark = 'GSL'
    elif message.text == 'Показать всё':
        current_list = current_table.all_items
        mark = 'DIF'
    await request_service(message, current_list, mark)


# Фоновая обработка добавления записи в список
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    item = call.data[3:]
    current_table.set_actual(item)
    await call.answer(f'Нужно:  {call.data[3:]} \U0001F44C')
    not_actual_list = current_table.irrelevant_items
    await request_service(call, not_actual_list, 'ATL')


# Фоновая обработка удаления записи из списка
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    item = call.data[3:]
    current_table.set_irrelevant(item)
    await call.answer(f'Уже не нужно:  {call.data[3:]} \U0001F44C', cache_time=1)
    current_list = current_table.actual_items
    await request_service(call, current_list, 'GSL')


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    item = call.data[3:]
    current_table.delete_item(item)
    await call.answer(f'Удалено из записей: {call.data[3:]} \U0001F44C', cache_time=2)
    current_list = current_table.all_items
    await request_service(call, current_list, 'DIF')


async def request_service(request, current_list, code):
    """ Менеджер запросов """
    answer = await get_answer_type(request)
    txt = await get_answer_txt(current_list, code)
    markup = await get_markup(current_list, code)
    if code == 'ATL':
        markup.add(button_new)
    await answer(text=txt, reply_markup=markup)


async def get_answer_type(msg):
    """ Возвращает тип ответа """
    if isinstance(msg, types.Message):
        return msg.answer
    elif isinstance(msg, types.CallbackQuery):
        return msg.message.edit_text


async def get_answer_txt(current_list, list_code):
    """ Возвращает текст сообщения"""
    if list_code == 'ATL':
        # сообщения для списка неактуальных записей
        if current_list:
            return 'Что нужно добавить? \U0001F914 '
        return 'Выбирать не из чего... \U00002639'
    if list_code == 'GSL':
        # сообщения для списка актуальных записей
        if current_list:
            return 'Вот список! \U0001F609 \n' f'Ред. в {current_table.updated_time}'
        return 'Список пуст! \U0001F389 '
    if list_code == 'DIF':
        # сообщения для списка всех записей
        if current_list:
            return 'Что нужно удалить? \U0001F914 '
        return 'Удалять нечего! \U0001F923'


async def get_markup(current_list, list_code):
    """ Возвращает разметку кнопок """
    if current_list:
        btn_list = get_btns(current_list, list_code)
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup.add(*btn_list)
        return markup
    else:
        markup = InlineKeyboardMarkup()
        return markup


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new(call: types.CallbackQuery):
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


@dp.message_handler(filter_users, commands='blocked')
async def show_blocked(message: types.Message):
    markup = InlineKeyboardMarkup()
    clear_btn = InlineKeyboardMarkup(text='Очистить список', callback_data='clear_blocked')
    markup.add(clear_btn)
    msg = ''
    for item in blocked_list.blocked:
        msg += f'id: {item[0]}  datetime: {item[1]}  message: {item[2]}\n'
    await message.answer(msg, reply_markup=markup)


@dp.callback_query_handler(Text(equals='clear_blocked'))
async def clear_blocked_list(call: types.CallbackQuery):
    blocked_list.clear()
    await call.answer(f'Список очищен! \U0001F44C', cache_time=2)
    await call.message.delete()


# Фоновая обработка текста новой записи
@dp.message_handler(filter_users)
async def add_new_item(message: types.Message):
    global current_table
    if current_table is None:
        return await start_chat(message)
    txt_size = sys.getsizeof(message.text)
    msg_txt = None
    if txt_size > 128:
        await message.answer(f'Слишком много слов! \n'
                             f'Давай покороче... \U0001F612')
    elif message.text not in current_table.all_items:
        current_table.add_new_item(message.text)
        msg_txt = f'Добавлено: {message.text} \U0001F44C '
    else:
        msg_txt = f'Не повторяйся! \U0000261D'
    await message.answer(msg_txt)


# Доп. функция. Формирует список кнопок из передаваемого множества
def get_btns(set_type, prefix):
    global rows_count
    long_txt_flag = False
    btn_list = []
    for item in sorted(set_type):
        txt_size = sys.getsizeof(item)
        if txt_size > 100:
            long_txt_flag = True
        if prefix == "DIF":
            button_item = InlineKeyboardButton('\U0000274C  ' + item, callback_data=prefix + item)
        else:
            button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    if long_txt_flag:
        rows_count = 1
    else:
        rows_count = 2
    return btn_list


if __name__ == '__main__':
    executor.start_polling(dp)
