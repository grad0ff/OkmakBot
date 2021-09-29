import datetime

import config

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

import db_manage
from db_manage import ShoppingList, set_blocked_id

bot = Bot(token=config.token)
dp = Dispatcher(bot)

users = config.users

button_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')


# Фильтрация пользователей
async def filtering_users(message):
    user = message.chat.id
    if user not in users:
        set_blocked_id(user, message.text)
    return user not in users


# Запустить OkmakBot
@dp.message_handler(filtering_users)
@dp.message_handler(commands='start')
async def start(message: types.Message):
    global bot_status
    if message.chat.id in users:
        button_add = KeyboardButton('Добавить в список')
        button_all = KeyboardButton('Показать все записи')
        button_lst = KeyboardButton('Показать список')
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(button_add, button_lst)
        markup.add(button_all)
        await message.answer('Всегда готов! \U0001F44D', reply_markup=markup)


@dp.message_handler(Text(equals='admin'))
async def show_blocked_IDs(message: types.Message):
    await message.answer(shopping_list.blocked_id_list)


# Очистить чат
@dp.message_handler(commands='clear_chat')
async def clear_chat(message: types.Message):
    dt = db_manage.get_datetime()
    print(dt)
    # message.chat.message_auto_delete_time = datetime.time
    # await bot.delete_message(message.)
    await message.answer('Ощищено! \U0001F61C')
    # await message.answer('Пока вообще никак! \U0001F61C')


# Добавить товар в список покупок
@dp.message_handler(Text(equals='Добавить в список'))
async def add_to_list(message: types.Message):
    if shopping_list.not_purchased_list:
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.not_purchased_list, 'ATL'))
        markup.add(button_new)
        await message.answer('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(button_new)
        await message.answer('Выбирать не из чего... \U00002639', reply_markup=markup)


# Фоновая обработка добавления записи в список покупок
@dp.callback_query_handler(Text(startswith='ATL'))
async def atl(call: types.CallbackQuery):
    shopping_list.add_to_shoplist(call.data[3:])
    await call.answer(f'Нужно купить:  {call.data[3:]} \U0001F44C')
    markup = InlineKeyboardMarkup()
    markup.add(*display_btns(shopping_list.not_purchased_list, 'ATL'))
    markup.add(button_new)
    if shopping_list.not_purchased_list:
        await call.message.edit_text('Что же нужно купить? \U0001F914', reply_markup=markup)
    else:
        await call.message.edit_text('Выбирать не из чего... \U00002639', reply_markup=markup)
    await call.answer()


# Показать список покупок
@dp.message_handler(Text(equals='Показать список'))
async def get_shopping_list(message: types.Message):
    if shopping_list.shoplist:
        markup = InlineKeyboardMarkup()
        markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
        await message.answer(
            f'Вот тебе список! \U0001F609 \nРед. {shopping_list.datetime}', reply_markup=markup
        )
    else:
        await message.answer('Список покупок пуст! \U0001F389')


# Фоновая обработка показа списка покупок
@dp.callback_query_handler(Text(startswith='GSL'))
async def gsl(call: types.CallbackQuery):
    shopping_list.del_from_shoplist(call.data[3:])
    markup = InlineKeyboardMarkup()
    markup.add(*(display_btns(shopping_list.shoplist, 'GSL')))
    await call.answer(f'Куплено:  {call.data[3:]} \U0001F44C', cache_time=1)
    if shopping_list.shoplist:
        await call.message.edit_text('Вот тебе список! \U0001F609', reply_markup=markup)
    else:
        await call.message.edit_text('Список покупок пуст! \U0001F389')
    await call.answer()


# Показать все продукты
@dp.message_handler(Text(equals='Показать все записи'))
async def show_all_list(message):
    if shopping_list.products:
        markup = InlineKeyboardMarkup()
        markup.add(*display_btns(shopping_list.products, 'DIF'))
        await message.answer(
            'Вот тебе все записи! \U0001F60E \n'
            'Для удаления записи нажми на элемент... \U0001F447', reply_markup=markup
        )
    else:
        await message.answer('А записей нет! \U0001F602')


# Фоновая обработка удаления записи
@dp.callback_query_handler(Text(startswith='DIF'))
async def dif(call: types.CallbackQuery):
    shopping_list.delete_item(call.data[3:])
    markup = InlineKeyboardMarkup()
    markup.add(*(display_btns(shopping_list.products, 'DIF')))
    if shopping_list.products:
        await call.message.edit_text(f'Удалено из записей: {call.data[3:]} \U0001F44C', reply_markup=markup)
    else:
        await call.message.edit_text('Удалять нечего! \U0001F923')
    await call.answer()


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new_item(call: types.CallbackQuery):
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


# Фоновая обработка текста новой записи
@dp.message_handler(filtering_users)
@dp.message_handler()
async def add_new_item(message: types.Message):
    if message.text not in shopping_list.products:
        shopping_list.add_new_item(message.text)
        await message.answer(f'Добавлено: {message.text} \U0001F44C')
    else:
        await message.answer(f'Не повторяйся! \U0000261D')


# Доп. функция. Формирует список кнопок из передаваемого множества
def display_btns(set_type, prefix):
    btn_list = []
    for item in sorted(set_type):
        button_item = InlineKeyboardButton(item, callback_data=prefix + item)
        btn_list.append(button_item)
    return btn_list


if __name__ == '__main__':
    shopping_list = ShoppingList()
    executor.start_polling(dp)
