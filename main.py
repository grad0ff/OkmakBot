import asyncio
import sys
import logging
import zipfile

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from db_manage import ShoppingList, ToDoList, BlockedUsers
from config import *

logging.basicConfig(filename=log_file, filemode='w')
bot = Bot(token=token)
dp = Dispatcher(bot)
users_list = list(users.values())

shopping_list = ShoppingList()
todo_list = ToDoList()
current_table = None
button_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')
rows_count = 2


# Фильтрация пользователей
async def filtering_users(message: types.Message):
    user = message.from_user.id
    if user not in users_list:
        BlockedUsers.set_blocked_id(user, message.text)
    else:
        return message


# Запустить OkmakBot
@dp.message_handler(filtering_users, commands='start')
async def run_chat(message: types.Message):
    global current_table
    await message.answer(f'Всегда готов! \U0001F44D \n')
    await asyncio.sleep(0.25)
    await start_chat(message)
    await asyncio.sleep(600)
    current_table = None
    # await bot.send_message(message.chat.id, 'Всё! \nЯ спать... \U0001F634', allow_sending_without_reply=True,
    #                        disable_notification=True, reply_markup=ReplyKeyboardRemove(True))
    last_msg = await bot.send_message(message.chat.id, text='Всё! \nЯ спать... \U0001F634',
                                      allow_sending_without_reply=True,
                                      disable_notification=True, reply_markup=ReplyKeyboardRemove(True))
    await last_msg.delete()


@dp.message_handler(Text(startswith='Выход из'))
async def start_chat(message: types.Message):
    global current_table
    current_table = None
    button_shop = KeyboardButton('Покупки')
    button_todo = KeyboardButton('Дела')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(button_shop)
    markup.add(button_todo)

    # markup = await get_start_kb()
    # txt = ''
    # if not message.text.startswith('Выход из'):
    # await message.answer(f'{txt}Выбери нужный раздел \U0001F4C2', reply_markup=markup)
    await message.answer(f'Выбери нужный раздел \U0001F4C2', reply_markup=markup)


# async def get_start_kb():
#     button_shop = KeyboardButton('Покупки')
#     button_todo = KeyboardButton('Дела')
#     markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
#     markup.add(button_shop)
#     markup.add(button_todo)
#     return markup


# Выбрать вид
@dp.message_handler(Text(equals=['Покупки', 'Дела']))
async def select_type(message: types.Message):
    global current_table, rows_count
    if message.text == 'Покупки':
        current_table = shopping_list
        message.text = 'Покупок'
        rows_count = 2
    elif message.text == 'Дела':
        current_table = todo_list
        message.text = 'Дел'
        rows_count = 1
    button_add = KeyboardButton('Внести в список')
    button_lst = KeyboardButton('Показать список')
    button_all = KeyboardButton('Показать всё')
    button_exit = KeyboardButton(f'Выход из {message.text}')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(button_add, button_lst)
    markup.add(button_all, button_exit)
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)


# Добавить в список
@dp.message_handler(Text(equals='Внести в список'))
async def add_to_list(message: types.Message):
    if current_table.not_in_actual_list:
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup.add(*display_btns(current_table.not_in_actual_list, 'ATL'))
        markup.add(button_new)
        await message.answer('Что нужно добавить? \U0001F914', reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(button_new)
        await message.answer('Выбирать не из чего... \U00002639', reply_markup=markup)


# Фоновая обработка добавления записи в список
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    current_table.add_to_shoplist(call.data[3:])
    await call.answer(f'Нужно:  {call.data[3:]} \U0001F44C')
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*display_btns(current_table.not_in_actual_list, 'ATL'))
    markup.add(button_new)
    if current_table.not_in_actual_list:
        await call.message.edit_text('Что нужно добавить? \U0001F914', reply_markup=markup)
    else:
        await call.message.edit_text('Выбирать не из чего... \U00002639', reply_markup=markup)
    await call.answer()


# Показать список
@dp.message_handler(Text(equals='Показать список'))
async def get_current_table(message: types.Message):
    if current_table.actual_list:
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup.add(*(display_btns(current_table.actual_list, 'GSL')))
        await message.answer(
            f'Вот список! \U0001F609 \nРед. {current_table.datetime}', reply_markup=markup
        )
    else:
        await message.answer('Список пуст! \U0001F389')


# Фоновая обработка показа списка
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    current_table.del_from_shoplist(call.data[3:])
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*(display_btns(current_table.actual_list, 'GSL')))
    await call.answer(f'Уже не нужно:  {call.data[3:]} \U0001F44C', cache_time=1)
    if current_table.actual_list:
        await call.message.edit_text('Вот список! \U0001F609', reply_markup=markup)
    else:
        await call.message.edit_text('Список пуст! \U0001F389')
    await call.answer()


# Показать все записи
@dp.message_handler(Text(equals='Показать всё'))
async def show_all_list(message):
    if current_table.all_items:
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup.add(*display_btns(current_table.all_items, 'DIF'))
        await message.answer(
            'Вот тебе все записи! \U0001F60E \n'
            'Для удаления записи нажми на элемент... \U0001F447', reply_markup=markup
        )
    else:
        await message.answer('А записей нет! \U0001F602')


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    current_table.delete_item(call.data[3:])
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*(display_btns(current_table.all_items, 'DIF')))
    if current_table.all_items:
        await call.message.edit_text(f'Удалено из записей: {call.data[3:]} \U0001F44C', reply_markup=markup)
    else:
        await call.message.edit_text('Удалять нечего! \U0001F923')
    await call.answer()


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new(call: types.CallbackQuery):
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


@dp.message_handler(filtering_users, commands='blocked')
async def show_blocked_users(message: types.Message):
    blocked = BlockedUsers.get_blocked()
    markup = InlineKeyboardMarkup()
    clear_btn = InlineKeyboardMarkup(text='Очистить список', callback_data='clear_blocked')
    markup.add(clear_btn)
    for item in blocked:
        msg = f'id:  {item[0]}\n' \
              f'datetime:  {item[1]}\n' \
              f'message:  {item[2]}'
        await message.answer(msg)
    await message.answer(text='0', reply_markup=markup)


@dp.message_handler(filtering_users, commands='log')
async def show_blocked_users(message: types.Message):
    await message.answer_document( )


@dp.callback_query_handler(Text(equals='clear_blocked'))
async def clear_blocked_list(call: types.CallbackQuery):
    BlockedUsers.clear_list()
    await call.message.delete()


# Фоновая обработка текста новой записи
@dp.message_handler(filtering_users)
async def add_new_item(message: types.Message):
    global current_table
    if current_table is None:
        await start_chat(message)
    elif sys.getsizeof(message.text) > 128:
        await message.answer(f'Слишком много слов! \nДавай покороче... \U0001F612')
    elif message.text not in current_table.all_items:
        current_table.add_new_item(message.text)
        await message.answer(f'Добавлено: {message.text} \U0001F44C')
    else:
        await message.answer(f'Не повторяйся! \U0000261D')


# # Очистить чат
# @dp.message_handler(commands='clear_chat')
# async def clear_chat(message: types.Message):
#     # dt = db_manage.get_datetime()
#     # message.chat.message_auto_delete_time = datetime.time
#     # await bot.delete_message(message.)
#     await message.answer('Ощищено! \U0001F61C')
#     # await message.answer('Пока вообще никак! \U0001F61C')


# Доп. функция. Формирует список кнопок из передаваемого множества
def display_btns(set_type, prefix):
    btn_list = []
    for i in sorted(set_type):
        if prefix == "DIF":
            button_item = InlineKeyboardButton('< ' + i + ' >', callback_data=prefix + i)
        else:
            button_item = InlineKeyboardButton(i, callback_data=prefix + i)
        btn_list.append(button_item)
    return btn_list


if __name__ == '__main__':
    executor.start_polling(dp)
