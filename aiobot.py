from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from config import okmakbot_token
from shoping import ShoppingList

import pickle

shopping_list = ShoppingList()

bot = Bot(token=okmakbot_token)
dp = Dispatcher(bot)

button_new = KeyboardButton('*НОВОЕ*', callback_data='new_item')
button_back = KeyboardButton('*НАЗАД*', callback_data='go_back')
button_del = KeyboardButton('*УДАЛИТЬ*', callback_data='del_item')
func_buttons = [button_new, button_back, button_del]


# запустить Telegram бот
@dp.message_handler(commands='start')
@dp.message_handler(regexp='Назад')
async def start(message: types.Message):
    button_1 = KeyboardButton('Добавить в список')
    button_2 = KeyboardButton('Показать список')
    button_4 = KeyboardButton('Показать все записи')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(button_1, button_2)
    markup.add(button_4)
    if message.text == 'Назад':
        await message.answer('Что дальше? 😏', reply_markup=markup)
    else:
        await message.answer('Всегда готов! 👍', reply_markup=markup)


# Добавить товар в список
@dp.message_handler(regexp='Добавить в список')
async def add_to_list(message: types.Message):
    if shopping_list.not_added_list:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
        markup.add(button_new, button_del)
        await message.answer('Что же нужно купить? 🤔', reply_markup=markup)
    else:
        await message.answer('Больше нечего добавить... 😱')


@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    print('ATL')
    shopping_list.add_to_shoplist(call.data[3:])
    await add_to_list(call.message)
    await call.answer()


# Показать список покупок
@dp.message_handler(regexp='Показать список')
async def get_shopping_list(message: types.Message):
    if shopping_list.shoplist:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
        markup.add(button_new, button_del)
        await message.answer('Вот тебе список: 😉', reply_markup=markup)
    else:
        await message.answer('Список покупок пуст! 😁')


@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    print('GSL')
    shopping_list.del_from_shoplist(call.data[3:])
    await get_shopping_list(call.message)
    await call.answer()


# Показать все продукты
@dp.message_handler(regexp='Показать все записи')
async def show_all_list(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*display_btns(shopping_list.get_all_items(), 'SAL'))
    markup.add(button_del)
    await message.answer('Вот тебе все записи! 😎', reply_markup=markup)


@dp.callback_query_handler(Text(startswith='SAL'))
async def gsl(call: types.CallbackQuery):
    print('SAL')
    await call.answer()


@dp.callback_query_handler(Text(startswith='del_item'))
async def del_item_forever(call: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.get_all_items(), 'DIF'))
    markup.add(button_back)
    await call.message.answer('Что будем удалять? 😳', reply_markup=markup)
    await call.answer()


@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    print('DIF')
    shopping_list.delete_item(call.data[3:])
    await del_item_forever(call)
    print(call.data[3:])
    await call.answer()


# Добавить новую запись в список
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new_item(call: types.CallbackQuery):
    print('*НОВОЕ*')
    await call.message.answer('Просто напиши... 👇')
    await call.answer()


@dp.message_handler()
async def ani(message: types.Message):
    if message.text not in shopping_list.get_all_items():
        shopping_list.add_new_item(message.text)
        await message.answer(f'Добавлено:  {message.text}')
    else:
        await message.answer(f'Не повторяйся! ☝️')


# Формирует список из множества
def display_btns(set_type, prefix):
    btn_list = []
    for item in sorted(set_type):
        button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    return btn_list


with open('items.db', 'wb') as db:
    pickle.dump({'all': shopping_list.get_all_items(), 'list': shopping_list.shoplist,
                 'not_added': shopping_list.not_added_list}, db)

# with open('items.db', 'rb') as db:
#     pickle.
executor.start_polling(dp)
