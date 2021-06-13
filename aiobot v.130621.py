import config
import pickle

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor, markdown
# from time import sleep
from shopping import ShoppingList

shopping_list = ShoppingList()

bot = Bot(token=config.token)
dp = Dispatcher(bot)

users = [389552179, 400358789]

button_new = InlineKeyboardButton('< НОВАЯ ЗАПИСЬ >', callback_data='new_item')
button_del = InlineKeyboardButton('< УДАЛИТЬ ЗАПИСЬ >', callback_data='del_item')
button_back = InlineKeyboardButton('< НАЗАД >', callback_data='get_back')


# Формирование клавиатуры главного меню
def start_kb(markup):
    button_atl = InlineKeyboardButton('Добавить в список', callback_data='add_to_list')
    button_ssl = InlineKeyboardButton('Показать список', callback_data='show_shopping_list')
    button_sai = InlineKeyboardButton('Показать все записи', callback_data='show_all_items')
    markup.add(button_atl, button_ssl)
    markup.add(button_sai)


# Фильтрация пользователей
async def filtering_users(message: types.Message):
    return message.chat.id not in users


# Запустить OkmakBot
@dp.message_handler(filtering_users)
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = InlineKeyboardMarkup()
    start_kb(markup)
    await message.answer('Всегда готов! \U0001F44D', reply_markup=markup)


# Очистить чат
@dp.message_handler(commands='clear')
async def clear_chat(message: types.Message):
    await message.answer('Пока вообще никак! \U0001F61C')


# Фоновая обработка нажатия кнопок
@dp.callback_query_handler(Text(equals='add_to_list'))
async def add_to_list(call: types.CallbackQuery):
    # Добавить товар в список покупок
    print('add_to_list')
    markup = InlineKeyboardMarkup()
    if shopping_list.not_added_list:
        markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
        markup.add(button_new, button_back)
        await call.message.edit_text('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        markup.add(button_new, button_back)
        await call.message.edit_text('Выбирать не из чего... \U00002639', reply_markup=markup)
    await call.answer()


# Фоновая обработка добавления записи в список покупок
@dp.callback_query_handler(Text(contains='ATL'))
async def atl(call: types.CallbackQuery):
    print('ATL')
    shopping_list.add_to_shoplist(call.data[3:])
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
    markup.add(button_new, button_back)
    if shopping_list.not_added_list:
        await call.message.edit_text('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        await call.message.edit_text('Выбирать не из чего... \U00002639', reply_markup=markup)
    await call.answer(f'Нужно купить:  {call.data[3:]} \U0001F44C')
    await call.answer()
    save_data()


# Показать список покупок
@dp.callback_query_handler(Text(equals='show_shopping_list'))
async def show_shopping_list(call: types.CallbackQuery):
    print('show_shopping_list')
    markup = InlineKeyboardMarkup()
    markup.add(*(display_btns(shopping_list.shoplist, 'SSL')))
    markup.add(button_back)
    if shopping_list.shoplist:
        await call.message.edit_text('Вот тебе список: \U0001F609', reply_markup=markup)
    else:
        await call.message.edit_text('Список покупок пуст! \U0001F389', reply_markup=markup)
    await call.answer()


# Фоновая обработка показа списка покупок
@dp.callback_query_handler(Text(contains='SSL'))
async def ssl(call: types.CallbackQuery):
    print('SSL')
    shopping_list.del_from_shoplist(call.data[3:])
    markup = InlineKeyboardMarkup()
    markup.add(*(display_btns(shopping_list.shoplist, 'SSL')))
    markup.add(button_back)
    await call.answer(f'Куплено:  {call.data[3:]} \U0001F44C', cache_time=1)
    if shopping_list.shoplist:
        await call.message.edit_text('Вот тебе список: \U0001F609', reply_markup=markup)
    else:
        await call.message.edit_text('Список покупок пуст! \U0001F389', reply_markup=markup)
    save_data()
    await call.answer()


@dp.callback_query_handler(Text(equals='show_all_items'))
async def show_all_items(call: types.CallbackQuery):
    # Показать все продукты
    print('show_all_items')
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.get_all_items(), 'SAI'))
    if shopping_list.get_all_items():
        markup.add(button_del, button_back)
        await call.message.edit_text('Вот тебе все записи! \U0001F60E', reply_markup=markup)
    else:
        markup.add(button_back)
        await call.message.edit_text('А записей нет! \U0001F923', reply_markup=markup)
    await call.answer()


@dp.callback_query_handler(Text(contains='SAI'))
async def sai(call: types.CallbackQuery):
    await call.answer()


# Фоновая обработка кнопки удаления записи
@dp.callback_query_handler(Text(equals='del_item'))
async def del_item(call: types.CallbackQuery):
    print('del_item')
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.get_all_items(), 'DIF'))
    markup.add(button_back)
    if shopping_list.get_all_items():
        await call.message.edit_text('Что будем удалять? \U0001F62C', reply_markup=markup)
    else:
        await call.message.edit_text('А записей нет! \U0001F923', reply_markup=markup)
    await call.answer()


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(contains='DIF'))
async def dif(call: types.CallbackQuery):
    print('DIF')
    shopping_list.delete_item(call.data[3:])
    await call.answer(f'Удалено из записей: {call.data[3:]} \U0001F44C', cache_time=1)
    save_data()
    await del_item(call)
    await call.answer()


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(equals='new_item'))
async def new_item(call: types.CallbackQuery):
    print('*НОВАЯ ЗАПИСЬ*')
    markup = InlineKeyboardMarkup()
    markup.add(button_back)
    await call.message.edit_text('Просто напиши сообщение... \U0001F447', reply_markup=markup)
    await call.answer()


# Вернуться в главное меню
@dp.callback_query_handler(Text(equals='get_back'))
async def get_back(call: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    start_kb(markup)
    await call.message.edit_text('Всегда готов! \U0001F44D', reply_markup=markup)
    await call.answer()


@dp.message_handler()
async def add_new_item(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(button_back)
    if message.text not in shopping_list.get_all_items():
        shopping_list.add_new_item(message.text)
        await message.answer(f'Добавлено: {message.text} \U0001F44C', reply_markup=markup)
        save_data()
    else:
        await message.answer(f'Не повторяйся! \U0000261D', reply_markup=markup)


# Доп. функция. Формирует список кнопок из передаваемого множества
def display_btns(set_type, prefix):
    btn_list = []
    for item in sorted(set_type):
        button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    return btn_list


def save_data():
    with open('data.pkl', 'wb') as dumper:
        pickle.dump(shopping_list, dumper, protocol=pickle.HIGHEST_PROTOCOL)


def load_data():
    global shopping_list
    with open('data.pkl', 'rb') as loader:
        shopping_list = pickle.load(loader)


if __name__ == '__main__':
    load_data()
    # save_data()
    executor.start_polling(dp)
