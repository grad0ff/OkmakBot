import config

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from db_manage import ShoppingList, ToDoList, BlockedUsers

bot = Bot(token=config.token)
dp = Dispatcher(bot)
users = config.users

shoppinglist = ShoppingList()
todo_list = ToDoList()
blocked_list = BlockedUsers()

button_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')
current_table = None
rows_count = 2
status = 'Куплено'
action = 'купить'


# Фильтрация пользователей
async def filtering_users(message):
    user = message.chat.id
    if user not in users:
        blocked_list.set_blocked_id(user, message.text)
    return user not in users


# Запустить OkmakBot
@dp.message_handler(filtering_users)
@dp.message_handler(commands='start')
@dp.message_handler(Text(startswith='Выход из'))
async def start(message: types.Message):
    global current_table
    if message.chat.id in users:
        button_shop = KeyboardButton('Покупки')
        button_todo = KeyboardButton('Дела')
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(button_shop)
        markup.add(button_todo)
        txt = ''
        if message.text.startswith('Выход из'):
            current_table = None
        else:
            txt = 'Всегда готов! \U0001F44D'
        await message.answer(f'{txt} \nВыбери нужный раздел \U0001F4C2', reply_markup=markup)


# Выбрать вид
@dp.message_handler(Text(equals=['Покупки', 'Дела']))
async def start(message: types.Message):
    global current_table, rows_count, status, action
    button_exit_txt = ''
    if message.text == 'Покупки':
        current_table = shoppinglist
        button_exit_txt = 'Покупок'
        action = 'купить'
        status = 'Куплено'
        rows_count = 2
    elif message.text == 'Дела':
        current_table = todo_list
        button_exit_txt = 'Дел'
        status = 'Сделано'
        action = 'сделать'
        rows_count = 1
    button_add = KeyboardButton('Внести в список')
    button_lst = KeyboardButton('Показать список')
    button_all = KeyboardButton('Показать всё')
    button_exit = KeyboardButton(f'Выход из {button_exit_txt}')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(button_add, button_lst)
    markup.add(button_all, button_exit)
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)


# Переход в раздел добавления элементов в список покупок/дел
@dp.message_handler(Text(equals='Внести в список'))
async def add_to_list(message: types.Message):
    msg_data = handling_add()
    await message.answer(msg_data['text'], reply_markup=msg_data['markup'])


# Обработка добавления элемента в список покупок/дел
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    current_table.add_to_shoplist(call.data[3:])
    await call.answer(f'Нужно {action}:  {call.data[3:]} \U0001F44C')
    msg_data = handling_add()
    await call.message.edit_text(msg_data['text'], reply_markup=msg_data['markup'])
    await call.answer()


# Отображение раздела добавления элементов в список покупок/дел
def handling_add():
    data = dict()
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*display_btns(current_table.not_in_actual_list, 'ATL'))
    markup.add(button_new)
    data['markup'] = markup
    if current_table.not_in_actual_list:
        text = f'Что нужно {action}? \U0001F914'
    else:
        text = 'Выбирать не из чего... \U00002639'
    data['text'] = text
    return data


# Переход в раздел покупок/дел
@dp.message_handler(Text(equals='Показать список'))
async def get_current_table(message: types.Message):
    msg_data = handling_show()
    await message.answer(msg_data['text'], reply_markup=msg_data['markup'])


# Обработка удаления элемента из списка покупок/дел
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    current_table.del_from_shoplist(call.data[3:])
    await call.answer(f'{status}:  {call.data[3:]} \U0001F44C', cache_time=1)
    msg_data = handling_show()
    await call.message.edit_text(msg_data['text'], reply_markup=msg_data['markup'])
    await call.answer()


# Отображение раздела покупок/дел
def handling_show():
    data = dict()
    markup = InlineKeyboardMarkup(row_width=rows_count, )
    markup.add(*(display_btns(current_table.actual_list, 'GSL')))
    data['markup'] = markup
    if current_table.actual_list:
        text = f'Вот список! \U0001F609 \nРед. {current_table.datetime}'
    else:
        text = 'Список пуст! \U0001F389'
    data['text'] = text
    return data


# Переход в раздел со всеми записями из БД
@dp.message_handler(Text(equals='Показать всё'))
async def show_all_list(message):
    msg_data = handling_show_all()
    await message.answer(msg_data['text'], reply_markup=msg_data['markup'])


# Обработка удаления элемента из БД
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    current_table.delete_item(call.data[3:])
    await call.answer(f'Удалено:  {call.data[3:]} \U0001F44C', cache_time=1)

    msg_data = handling_show_all()
    await call.message.edit_text(msg_data['text'], reply_markup=msg_data['markup'])
    await call.answer()


# Отображение раздела со всеми записями из БД
def handling_show_all():
    data = dict()
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*display_btns(current_table.all_items, 'DIF'))
    data['markup'] = markup
    if current_table.all_items:
        text = 'Вот все записи! \U0001F60E \nДля удаления элемента нажми на него... \U0001F447'
    else:
        text = 'А записей нет! \U0001F602'
    data['text'] = text
    return data


# Обработка нажатия кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new(call: types.CallbackQuery):
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


# Обработка текста новой записи
@dp.message_handler(filtering_users)
@dp.message_handler()
async def add_new_item(message: types.Message):
    global current_table
    if current_table is None:
        await message.answer(f'Сначала выбери нужный раздел!  \U000026A0')
    elif message.text not in current_table.all_items:
        current_table.add_new_item(message.text)
        await message.answer(f'Добавлено: {message.text} \U0001F44C')
    else:
        await message.answer(f'Не повторяйся! \U0000261D')


# Отображение блокированных пользователей
@dp.message_handler(Text(equals='blocked'))
async def show_blocked_IDs(message: types.Message):
    await message.answer(blocked_list.get_blocked())


# Доп. функция. Формирует список кнопок из передаваемого множества
def display_btns(set_type, prefix):
    btn_list = []
    for i in sorted(set_type):
        button_item = InlineKeyboardButton(i, callback_data=prefix + i)
        btn_list.append(button_item)
    return btn_list


if __name__ == '__main__':
    executor.start_polling(dp)