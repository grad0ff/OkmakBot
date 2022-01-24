import asyncio
import sys
import logging
import config

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from db_manage import ShoppingList, ToDoList, BlockedUsers

logging.basicConfig(filename=config.log_file, filemode='w')

bot = Bot(token=config.token)
dp = Dispatcher(bot)
users_list = list(config.users.values())

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

    await asyncio.sleep(config.timer)
    current_table = None
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
    await message.answer(f'Выбери нужный раздел \U0001F4C2', reply_markup=markup)


# Выбрать вид списка
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


# Добавить запись в список
@dp.message_handler(Text(equals='Внести в список'))
async def add_to_list(message: types.Message):
    not_actual_list = current_table.get_notactual_list()
    await request_service(message, not_actual_list, 'ATL')


# Фоновая обработка добавления записи в список
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    current_table.add_to_list(call.data[3:])
    await call.answer(f'Нужно:  {call.data[3:]} \U0001F44C')
    not_actual_list = current_table.get_notactual_list()
    await request_service(call, not_actual_list, 'ATL')


# Показать список записей
@dp.message_handler(Text(equals='Показать список'))
async def get_current_table(message: types.Message):
    current_list = current_table.get_actual_list()
    await request_service(message, current_list, 'GSL')


# Фоновая обработка удаления записи из списка
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    current_table.del_from_list(call.data[3:])
    await call.answer(f'Уже не нужно:  {call.data[3:]} \U0001F44C', cache_time=1)
    current_list = current_table.get_actual_list()
    await request_service(call, current_list, 'GSL')


# Показать все записи
@dp.message_handler(Text(equals='Показать всё'))
async def show_all_list(message):
    current_list = current_table.get_all_list()
    await request_service(message, current_list, 'DIF')


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    current_table.delete_item(call.data[3:])
    await call.answer(f'Удалено из записей: {call.data[3:]} \U0001F44C', cache_time=2)
    current_list = current_table.get_all_list()
    await request_service(call, current_list, 'DIF')


# Очистить чат
@dp.message_handler(commands='clear')
async def clear_chat(message: types.Message):
    # dt = db_manage.get_datetime()
    # message.chat.message_auto_delete_time = datetime.time
    # await bot.delete_message(message.)
    await message.answer('Ощищено! \U0001F61C')
    # await message.answer('Пока вообще никак! \U0001F61C')


async def request_service(request, current_list, code):
    """ Менеджер запросов """
    answer = await get_answer_type(request)
    txt = await get_answer_txt(current_list, code)
    markup = await get_markup(current_list, code)
    if code == 'ATL':
        markup.add(button_new)
    await answer(text=txt, reply_markup=markup)


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
            return 'Вот список! \U0001F609 '
        return 'Список пуст! \U0001F389 '
    if list_code == 'DIF':
        # сообщения для списка всех записей
        if current_list:
            return 'Что нужно удалить? \U0001F914 '
        return 'Удалять нечего! \U0001F923'


async def get_answer_type(msg):
    """ Возвращает тип ответа"""
    if isinstance(msg, types.Message):
        return msg.answer
    elif isinstance(msg, types.CallbackQuery):
        return msg.message.edit_text


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
    # await message.answer_document()
    pass


@dp.callback_query_handler(Text(equals='clear_blocked'))
async def clear_blocked_list(call: types.CallbackQuery):
    BlockedUsers.clear_list()
    await call.message.delete()


# Фоновая обработка текста новой записи
@dp.message_handler(filtering_users)
async def add_new_item(message: types.Message):
    global current_table
    if current_table is None:
        return await start_chat(message)
    txt_size = sys.getsizeof(message.text)
    msg_txt = None
    if txt_size > 128:
        await message.answer(f'Слишком много слов! \n'
                             f'Давай покороче... \U0001F612')
    elif message.text not in current_table.get_all_list():
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
            button_item = InlineKeyboardButton('< ' + item + ' >', callback_data=prefix + item)
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
