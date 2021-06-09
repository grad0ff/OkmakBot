from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from shoping import ShoppingList

shopping_list = ShoppingList()

bot = Bot(token='1825854132:AAGdHn2rOseD9G8ky7V1XPpBzbrMYAqjNmw')
dp = Dispatcher(bot)

button_new = KeyboardButton('*НОВОЕ*', callback_data='new_item')
button_del = KeyboardButton('*УДАЛИТЬ*', callback_data='del_item')

base_markup = []


# запустить Telegram бот
@dp.message_handler(commands='start')
async def start(message: types.Message):
    global base_markup
    button_1 = InlineKeyboardButton('Добавить в список', callback_data='ATL')
    button_2 = InlineKeyboardButton('Показать список', callback_data='SSL')
    button_4 = InlineKeyboardButton('Показать все записи', callback_data='SAL')
    base_markup = InlineKeyboardMarkup(resize_keyboard=True)
    base_markup.add(button_1, button_2)
    base_markup.add(button_4)
    await message.answer('Всегда готов! \U0001F44D', reply_markup=base_markup)


@dp.callback_query_handler(Text(startswith='SAL'))
async def gsl(call: types.CallbackQuery):
    print('SAL')
    if shopping_list.get_all_items():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*display_btns(shopping_list.get_all_items(), 'SAL'))
        markup.add(button_del)
        await call.message.edit_text('Вот тебе все записи! \U0001F60E', reply_markup=markup)
    else:
        await call.message.answer('А записей нет! \U0001F923', reply_markup=base_markup)
    await call.answer()


# Формирует список из множества
def display_btns(set_type, prefix):
    btn_list = []
    for item in sorted(set_type):
        button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    return btn_list


executor.start_polling(dp)
