from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from time import sleep
from shopping import ShoppingList
import pickle

shopping_list = ShoppingList()

bot = Bot(token='1825854132:AAGdHn2rOseD9G8ky7V1XPpBzbrMYAqjNmw')
dp = Dispatcher(bot)

button_new = KeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')
button_del = KeyboardButton('УДАЛИТЬ ЗАПИСЬ', callback_data='del_item')


# Запустить OkmakBot
@dp.message_handler(commands='start')
async def start(message: types.Message):
    sleep(0.25)
    button_1 = KeyboardButton('Добавить в список')
    button_2 = KeyboardButton('Показать список')
    button_4 = KeyboardButton('Показать все записи')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(button_1, button_2)
    markup.add(button_4)
    await message.answer('Всегда готов! \U0001F44D', reply_markup=markup)


# Добавить товар в список покупок
@dp.message_handler(regexp='Добавить в список')
async def add_to_list(message: types.Message):
    sleep(0.25)
    if shopping_list.not_added_list:
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
        markup.add(button_new)
        await message.answer('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(button_new)
        await message.answer('Выбирать не из чего... \U00002639', reply_markup=markup)


# Фоновая обработка добавления записи в список покупок
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    sleep(0.25)
    print('ATL')
    shopping_list.add_to_shoplist(call.data[3:])
    await call.answer(f'Нужно купить:  {call.data[3:]} \U0001F44C')
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
    markup.add(button_new)
    if shopping_list.not_added_list:
        await call.message.edit_text('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        await call.message.edit_text('Выбирать не из чего... \U00002639', reply_markup=markup)
    await call.answer()
    save_data()


# Показать список покупок
@dp.message_handler(regexp='Показать список')
async def get_shopping_list(message: types.Message):
    sleep(0.25)
    if shopping_list.shoplist:
        markup = InlineKeyboardMarkup()
        markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
        await message.answer('Вот тебе список: \U0001F609', reply_markup=markup)
    else:
        await message.answer('Список покупок пуст! \U0001F389')


# Фоновая обработка показа списка покупок
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    sleep(0.25)
    print('GSL')
    shopping_list.del_from_shoplist(call.data[3:])
    markup = InlineKeyboardMarkup()
    markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
    await call.answer(f'Куплено:  {call.data[3:]} \U0001F44C', cache_time=1)
    if shopping_list.shoplist:
        await call.message.edit_text('Вот тебе список: \U0001F609', reply_markup=markup)
    else:
        await call.message.edit_text('Список покупок пуст! \U0001F389')
    await call.answer()
    save_data()


# Показать все продукты
@dp.message_handler(regexp='Показать все записи')
async def show_all_list(message):
    sleep(0.25)
    if shopping_list.get_all_items():
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.get_all_items(), 'SAL'))
        markup.add(button_del)
        await message.answer('Вот тебе все записи! \U0001F60E', reply_markup=markup)
    else:
        await message.answer('А записей нет! \U0001F923')


# Фоновая обработка показа все записей
@dp.callback_query_handler(Text(startswith='SAL'))
async def gsl(call: types.CallbackQuery):
    print('SAL')
    await call.answer('Выбери что-то другое? \U0001F9D0')
    await call.answer()


# Фоновая обработка кнопки удаления записи
@dp.callback_query_handler(Text(startswith='del_item'))
async def del_item_forever(call: types.CallbackQuery):
    sleep(0.25)
    if shopping_list.get_all_items():
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.get_all_items(), 'DIF'))
        await call.message.edit_text('Что будем удалять? \U0001F62C', reply_markup=markup)
    else:
        await call.message.edit_text('А записей нет! \U0001F923')
    await call.answer()


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    sleep(0.25)
    print('DIF')
    shopping_list.delete_item(call.data[3:])
    await call.answer(f'Удалено из записей: {call.data[3:]} \U0001F44C', cache_time=1)
    await del_item_forever(call)
    await call.answer()
    save_data()


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new_item(call: types.CallbackQuery):
    sleep(0.25)
    print('*НОВАЯ ЗАПИСЬ*')
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


# Фоновая обработка текста новой записи
@dp.message_handler()
async def ani(message: types.Message):
    sleep(0.25)
    if message.text not in shopping_list.get_all_items():
        shopping_list.add_new_item(message.text)
        await message.answer(f'Добавлено: {message.text} \U0001F44C')
        save_data()
    else:
        await message.answer(f'Не повторяйся! \U0000261D')


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
