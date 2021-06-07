from aiogram import Bot, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from config import okmakbot_token

from shoping import ShoppingList

shopping_list = ShoppingList()

bot = Bot(token=okmakbot_token)
dp = Dispatcher(bot)

three_buttons = [KeyboardButton('Новое', callback_data='new_item'),
                 KeyboardButton('Назад', callback_data='back_to_adding'),
                 KeyboardButton('Удалить', callback_data='del_item')]


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
    await message.answer('Всегда готов! 👍', reply_markup=markup)


# Добавить товар в список
@dp.message_handler(regexp='Добавить в список')
async def add_to_list(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*display_btns(shopping_list.not_added_list))
    markup.add(*three_buttons)
    await message.answer('Что же нужно купить? 🤔', reply_markup=markup)


# Показать список покупок
@dp.message_handler(regexp='Показать список')
async def get_shopping_list(message: types.Message):
    if shopping_list.shoplist:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*display_btns(shopping_list.shoplist))
        markup.add(*three_buttons)
        await message.answer('Вот тебе список: 😉', reply_markup=markup)
    else:
        await message.answer('Список покупок пуст! 😁')


# Показать все продукты
@dp.message_handler(regexp='Показать все записи')
async def show_all_list(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*display_btns(shopping_list.get_all_items()))
    markup.add(*three_buttons)
    await message.answer('Все записи из базы:', reply_markup=markup)


# Формирует список из множества
def display_btns(list_type):
    btn_list = []
    for item in sorted(list_type):
        button_item = types.InlineKeyboardButton(item, callback_data=item)
        btn_list.append(button_item)
    return btn_list


@dp.message_handler(regexp='Новое')
async def add_new_item(message: types.Message):
    pass


@dp.message_handler(regexp='Удалить')
async def del_item(message: types.Message):
    ReplyKeyboardRemove()
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.get_all_items()))
    markup.add(three_buttons[1])
    await message.answer('Что будем удалять? 😳', reply_markup=ReplyKeyboardRemove(selective=True)
)


@dp.callback_query_handler(add_to_list)
async def test():
    print('call')


executor.start_polling(dp)
