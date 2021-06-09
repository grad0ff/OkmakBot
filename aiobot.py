from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from time import sleep
from shoping import ShoppingList

shopping_list = ShoppingList()

bot = Bot(token='1825854132:AAGdHn2rOseD9G8ky7V1XPpBzbrMYAqjNmw')
dp = Dispatcher(bot)

button_new = KeyboardButton('НОВОЕ', callback_data='new_item')
button_del = KeyboardButton('УДАЛИТЬ ЗАПИСЬ', callback_data='del_item')


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
    sleep(0.5)
    if message.text == 'Назад':
        await message.answer('Что дальше? \U0001F60F', reply_markup=markup)
    else:
        await message.answer('Всегда готов! \U0001F44D', reply_markup=markup)


# Добавить товар в список
@dp.message_handler(regexp='Добавить в список')
async def add_to_list(message: types.Message):
    markup = InlineKeyboardMarkup(row_width=2)
    sleep(0.5)
    if shopping_list.not_added_list:
        markup.add(*display_btns(shopping_list.not_added_list, 'ATL'))
        markup.add(button_new)
        await message.answer('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        markup.add(button_new)
        await message.answer('Тут уж без вариантов... \U00002639', reply_markup=markup)


# Фоновая обработка добваления в список покупок
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    print('ATL')
    shopping_list.add_to_shoplist(call.data[3:])
    sleep(0.5)
    await add_to_list(call.message)
    await call.answer()


# Показать список покупок
@dp.message_handler(regexp='Показать список')
async def get_shopping_list(message: types.Message):
    sleep(0.5)
    if shopping_list.shoplist:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
        await message.answer('Вот тебе список: \U0001F609', reply_markup=markup)
    else:
        await message.answer('Список покупок пуст! \U0001F601')


# Фоновая обработка показа списка покупок
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    print('GSL')
    shopping_list.del_from_shoplist(call.data[3:])
    await get_shopping_list(call.message)
    await call.answer()


# Показать все продукты
@dp.message_handler(regexp='Показать все записи')
async def show_all_list(message):
    sleep(0.5)
    if shopping_list.get_all_items():
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*display_btns(shopping_list.get_all_items(), 'SAL'))
        markup.add(button_del)
        await message.answer('Вот тебе все записи! \U0001F60E', reply_markup=markup)
    else:
        await message.answer('А записей нет! \U0001F923')


# Фоновая обработка: показ все записей
@dp.callback_query_handler(Text(startswith='SAL'))
async def gsl(call: types.CallbackQuery):
    print('SAL')
    await call.answer()


# Фоновая обработка кнопки удаления записи
@dp.callback_query_handler(Text(startswith='del_item'))
async def del_item_forever(call: types.CallbackQuery):
    sleep(0.5)
    if shopping_list.get_all_items():
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.get_all_items(), 'DIF'))
        await call.message.answer('Что будем удалять? \U0001F62C', reply_markup=markup)
    else:
        await call.message.answer('А записей нет! \U0001F923')
    await call.answer()


# Фоновая обработка: удаление записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    print('DIF')
    shopping_list.delete_item(call.data[3:])
    sleep(0.5)
    await call.message.answer(f'Удалено:  {call.data[3:]} \U0001F44C')
    await del_item_forever(call)
    print(call.data[3:])

    await call.answer()


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new_item(call: types.CallbackQuery):
    print('*НОВОЕ*')
    sleep(0.5)
    await call.message.answer('Просто напиши... \U0001F447')
    await call.answer()


# Фоновая обработка текста новой записи
@dp.message_handler()
async def ani(message: types.Message):
    sleep(0.5)
    if message.text.isalpha():
        if message.text not in shopping_list.get_all_items():
            shopping_list.add_new_item(message.text)
            await message.answer(f'Добавлено:  {message.text} \U0001F44C')
        else:
            await message.answer(f'Не повторяйся! \U0000261D')
    else:
        await message.answer(f'Буквами, пожалуйста! \U0001F620')


# Формирует список из множества
def display_btns(set_type, prefix):
    btn_list = []
    for item in sorted(set_type):
        button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    return btn_list


executor.start_polling(dp)
