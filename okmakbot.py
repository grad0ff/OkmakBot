import logging
import sys

from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove, Message, CallbackQuery
from aiogram.utils import executor

from service.chat_data import commands
from service.chat_data.buttons import *
from service.chat_data.states import *
from service.handle.db_manage import BaseList, Blocked
from service.handle.help import Help
from service.handle.preparing import Preparing
from service.service.config import Config

if sys.platform != 'win32':
    logging.basicConfig(filename=Config.LOG_FILE, filemode='w')

bot = Bot(token=Config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

shopping_list = BaseList('product')
task_list = BaseList('task')
blocked_list = Blocked('blocked')
db_table = shopping_list

users = list(Config.USERS.values())
rows_count = 1


async def filter_users(message: Message):
    """
    Фильтрует пользователей и возвращает сообщение если пользователь в списке зарегистрированных, иначе вносит в БД в
    таблицу незарегистрированных пользователей
    """
    user_id = message.from_user.id
    if user_id not in users:
        blocked_list.add(user_id, message.text)
    else:
        return message


@dp.message_handler(filter_users, commands=commands.START, state='*')
@dp.message_handler(Text(startswith=btn_back.text), state='*')
async def start_chat(message: Message, state: FSMContext):
    """
    Запускает бота и отображает основное меню
    """
    global db_table
    db_table = None
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(btn_shopping)
    markup.add(btn_tasks)
    await message.answer(f'Всегда готов!   \U0001F60E \n'
                         'Выбери нужный раздел   \U00002B07', reply_markup=markup)
    await state.finish()
    await AppState.wait_current_list.set()


@dp.message_handler(commands=commands.CANCEL, state='*')
async def cancel(message: Message, state: FSMContext):
    """
    Завершает чат и сбрасывает машину состояний
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Давай до свидания!   \U000026D4", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(filter_users, commands=commands.LOG, state='*')
async def get_log_file(message: Message):
    try:
        with open(Config.LOG_FILE, encoding='utf8', mode='a', ) as log_file:
            log_file.writelines([f'\n{"-" * 25}\n',
                                 f'{Help.get_datetime()} - ЛОГ ЗАПРОШЕН'])
        with open(Config.LOG_FILE, mode='rb') as log_file:
            markup = InlineKeyboardMarkup(row_width=rows_count)
            del_file_btn = InlineKeyboardButton(text='Очистить лог', callback_data='del_log')
            markup.add(del_file_btn)
            await message.answer_document(log_file, 'rb', reply_markup=markup)
    except FileNotFoundError:
        return await message.answer('Файл не найден')


@dp.callback_query_handler(Text(equals='del_log'), state='*')
async def del_log_file(call: CallbackQuery):
    with open(Config.LOG_FILE, encoding='utf8', mode='w') as log_file:
        log_file.writelines([f'{"-" * 25}\n',
                             f'{Help.get_datetime()} - ЛОГ ОЧИЩЕН'])
    await call.answer(f'Лог очищен!  \U0001F44C', cache_time=2)
    await call.message.delete()


@dp.message_handler(filter_users, commands=commands.BLOCKED, state='*')
async def show_blocked(message: Message):
    blacklist = blocked_list.blocked
    if blacklist:
        markup = InlineKeyboardMarkup(row_width=rows_count)
        clear_btn = InlineKeyboardButton(text='Очистить список', callback_data='clear_blocked')
        markup.add(clear_btn)
        answer_txt = str()
        for item in blacklist:
            answer_txt += f'id: {item[0]}  datetime: {item[1]}  message: {item[2]}\n'
        return await message.answer(answer_txt, reply_markup=markup)
    await message.answer('Список пуст')


@dp.callback_query_handler(Text(equals='clear_blocked'), state='*')
async def clear_blocked_list(call: CallbackQuery):
    blocked_list.clear()
    await call.answer(f'Список очищен!  \U0001F44C', cache_time=2)
    await call.message.delete()


@dp.message_handler(Text(equals=menu_btn_txt), state=[AppState.wait_current_list])
async def selected_current_list(message: Message, state: FSMContext):
    """
    Отображает пункты разделов, адаптирует текст кнопки выхода из раздела в соответствии с выбранным разделом
    """
    global db_table, rows_count
    msg_txt = message.text
    await state.update_data(current_list=msg_txt)
    if msg_txt == btn_shopping.text:
        db_table = shopping_list
        btn_back.text = 'Выйти из Покупок'
    elif msg_txt == btn_tasks.text:
        db_table = task_list
        btn_back.text = 'Выйти из Дел'
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_add, btn_show)
    markup.add(btn_all, btn_back)
    await message.answer('Выбери действие   \U00002B07', reply_markup=markup)
    await AppState.wait_action.set()


@dp.message_handler(Text(equals=submenu_btn_txt), state=[AppState.wait_action, *AppState.submenu_states])
async def selected_action(message: Message, state: FSMContext):
    """
    Отображает перечень действий, доступных для текущего списка
    """
    msg_txt = message.text
    await state.update_data(action=msg_txt)
    answer_txt = str()
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup_elements = list()

    if msg_txt == btn_add.text:
        irrelevant_items = db_table.irrelevant_items
        markup_elements = await Preparing.get_markup_btns(irrelevant_items)
        answer_txt = await Preparing.get_txt_for_irrelevant(irrelevant_items)
        await AppState.wait_add_to_list.set()

    if msg_txt == btn_show.text:
        actual_items = db_table.actual_items
        if actual_items[0]:
            markup_elements = await Preparing.get_markup_btns(actual_items[0], prefix='\U00002757', )
        if actual_items[1]:
            markup_elements.extend(await Preparing.get_markup_btns(actual_items[1]))
        answer_txt = await Preparing.get_txt_for_actual(actual_items, db_table.updated_time)
        await AppState.wait_del_from_list.set()

    if msg_txt == btn_all.text:
        all_items_list = db_table.all_items
        markup_elements = await Preparing.get_markup_btns(all_items_list, prefix='\U0000274C')
        answer_txt = await Preparing.get_txt_for_all(all_items_list)
        await AppState.wait_del_forever.set()

    markup.add(*markup_elements)
    await message.answer(answer_txt, reply_markup=markup)


@dp.callback_query_handler(state=AppState.wait_add_to_list)
async def add_to_list(call: CallbackQuery, state: FSMContext):
    """
    Фоновая обработка добавления записи из неактуального списка в актуальный, включая изменение статуса в БД
    """
    item = call.data
    await state.update_data(item=item)
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(btn_yes, btn_no)
    await call.message.edit_text('Это обязательно прям надо?  \U0001F631', reply_markup=markup)
    await AppState.wait_priority.set()


@dp.callback_query_handler(Text(equals=yn_btn_data), state=[AppState.wait_priority, AppState.wait_priority_new])
async def get_priority(call: CallbackQuery, state: FSMContext):
    data = call.data
    current_state = await state.get_state()
    priority = 1 if data == btn_yes.callback_data else 2
    item = (await state.get_data()).get('item')
    await call.answer(f'Нужно:   {item}  \U0001F44C')
    db_table.set_actual(item=item, priority=priority)
    if current_state == AppState.wait_priority_new.state:
        await call.message.delete()
    elif current_state == AppState.wait_priority.state:
        irrelevant_items_lists = db_table.irrelevant_items
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup_elements = await Preparing.get_markup_btns(irrelevant_items_lists)
        markup.add(*markup_elements)
        answer_txt = await Preparing.get_txt_for_irrelevant(irrelevant_items_lists)
        await call.message.edit_text(answer_txt, reply_markup=markup)
    await AppState.wait_add_to_list.set()


@dp.callback_query_handler(state=AppState.wait_del_from_list)
async def delete_from_list(call: CallbackQuery):
    """
    Фоновая обработка переноса записи из актуального списка в неактуальный, включая изменение статуса в БД
    """
    item = call.data
    db_table.set_irrelevant(item=item)
    await call.answer(f'Уже не нужно:   {item}  \U0001F44C', cache_time=1)
    actual_items_lists = db_table.actual_items
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup_elements = list()
    if actual_items_lists[0]:
        markup_elements = await Preparing.get_markup_btns(actual_items_lists[0], prefix='\U00002757')
        markup.add(*markup_elements)
    if actual_items_lists[1]:
        markup_elements = await Preparing.get_markup_btns(actual_items_lists[1])
        markup.add(*markup_elements)
    answer_txt = await Preparing.get_txt_for_actual(markup_elements, db_table.updated_time)
    await call.message.edit_text(answer_txt, reply_markup=markup)
    await AppState.wait_del_from_list.set()


@dp.callback_query_handler(state=AppState.wait_del_forever)
async def delete_forever(call: CallbackQuery):
    """
    Фоновая обработка удаления записи из полного списка и БД
    """
    item = call.data
    db_table.delete_item(item)
    await call.answer(f'Удалено из записей:  {item}  \U0001F44C', cache_time=2)
    all_items_lists = db_table.all_items
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup_elements = await Preparing.get_markup_btns(all_items_lists, prefix='\U0000274C')
    markup.add(*markup_elements)
    answer_txt = await Preparing.get_txt_for_all(markup_elements)
    await call.message.edit_text(answer_txt, reply_markup=markup)
    await AppState.wait_del_forever.set()


# Фоновая обработка текста новой записи
@dp.message_handler(filter_users, state='*')
async def adding_new_item(message: Message, state: FSMContext):
    global db_table
    msg_txt = message.text
    if await state.get_state() == AppState.wait_current_list.state:
        return await message.answer('Сначала выбери нужный раздел!  \U0001F4C2')
    if msg_txt in db_table.all_items:
        return await message.answer('Не повторяйся!  \U0000261D')
    if sys.getsizeof(msg_txt) > 128:
        return await message.answer('Слишком много слов!\n'
                                    'Давай покороче...  \U0001F612')
    else:
        await state.update_data(item=msg_txt)
        db_table.insert_new_item(msg_txt)
        markup = InlineKeyboardMarkup(row_width=rows_count)
        markup.add(btn_yes, btn_no)
        await message.answer('Это обязательно прям надо?  \U0001F631', reply_markup=markup)
        await AppState.wait_priority_new.set()


if __name__ == '__main__':
    executor.start_polling(dp)
