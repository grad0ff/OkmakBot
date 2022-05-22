import asyncio
import logging
import sys

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor

import config
from db_manage import Shopping, Task, Blocked

if sys.platform != 'win32':
    logging.basicConfig(filename=config.LOG_FILE, filemode='w')

storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

users = list(config.users.values())

shopping_list = Shopping()
task_list = Task()
blocked_list = Blocked()
current_table = shopping_list

button_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new_item')
rows_count = 2

kb_shopping = KeyboardButton('Покупки')
kb_tasks = KeyboardButton('Дела')

kb_add = KeyboardButton('Внести в список')
kb_show = KeyboardButton('Показать список')
kb_all = KeyboardButton('Показать всё')
kb_back = KeyboardButton('Назад')


class Step(StatesGroup):
    wait_current_list = State()
    wait_action = State()
    wait_add_to_list = State()
    wait_del_from_list = State()
    wait_del_forever = State()

    SUBMENU_STATES = (wait_add_to_list, wait_del_from_list, wait_del_forever)


async def filter_users(message: types.Message):
    """
    Фильтрует пользователей и возвращает сообщение если пользователь в списке зарегистрированных, иначе вносит в БД в
    таблицу незарегистрированных пользователей
    """
    user_id = message.from_user.id
    if user_id not in users:
        blocked_list.add(user_id, message.text)
    else:
        return message


@dp.message_handler(filter_users, commands='start', state='*')
@dp.message_handler(Text(equals=kb_back.text), state='*')
async def start_chat(message: types.Message, state: FSMContext):
    """
    Запускает бота и отображает основное меню
    """
    global current_table
    current_table = None
    await message.answer(f'Всегда готов! \U0001F44D \n')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(kb_shopping)
    markup.add(kb_tasks)
    await message.answer(f'Выбери нужный раздел \U0001F4C2', reply_markup=markup)
    await state.finish()
    await Step.wait_current_list.set()

    await asyncio.sleep(config.timer)
    current_table = None
    await message.answer(f'Я спать... \U0001F634', reply_markup=markup, disable_notification=True)


@dp.message_handler(commands='cancel', state='*')
async def cancel(message: types.Message, state: FSMContext):
    """
    Завершает чат и сбрасывает машину состояний
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Чат завершен", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(Text(equals=[kb_shopping.text, kb_tasks.text]), state=[Step.wait_current_list])
async def selected_current_list(message: types.Message, state: FSMContext):
    """
    Отображает пункты разделов, адаптирует текст кнопки выхода из раздела в соответствии с выбранным разделом
    """
    global current_table, rows_count
    msg = message.text
    await state.update_data(current_list=msg)

    if msg == kb_shopping.text:
        current_table = shopping_list
        rows_count = 2
    elif msg == kb_tasks.text:
        current_table = task_list
        rows_count = 1
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(kb_add, kb_show)
    markup.add(kb_all, kb_back)
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)
    await Step.wait_action.set()


@dp.message_handler(Text(equals=[kb_add.text, kb_show.text, kb_all.text]),
                    state=[Step.wait_action, *Step.SUBMENU_STATES])
async def selected_action(message: types.Message, state: FSMContext):
    """
    Отображает перечень действий, доступных для текущего списка

    """
    await state.update_data(action=message.text)

    current_list = list()
    msg = message.text
    if msg == kb_add.text:
        current_list = current_table.irrelevant_items
        await Step.wait_add_to_list.set()
    if msg == kb_show.text:
        current_list = current_table.actual_items
        await Step.wait_del_from_list.set()
    if msg == kb_all.text:
        current_list = current_table.all_items
        await Step.wait_del_forever.set()
    await request_manager(message, current_list, state)


# Фоновая обработка добавления записи в список
# @dp.callback_query_handler(Text(startswith='ATL'), state=Step.wait_add_to_list)
@dp.callback_query_handler(state=Step.wait_add_to_list)
async def add_to_list(call: types.CallbackQuery, state: FSMContext):
    item = call.data
    current_table.change_status(item, 'actual')
    await call.answer(f'Нужно:  {call.data[3:]} \U0001F44C')
    irrelevant_items_list = current_table.irrelevant_items
    await request_manager(call, irrelevant_items_list, state)


# Фоновая обработка удаления записи из списка
# @dp.callback_query_handler(Text(startswith='GSL'), state=Step.wait_del_from_list)
@dp.callback_query_handler(state=Step.wait_del_from_list)
async def show_list(call: types.CallbackQuery, state: FSMContext):
    item = call.data
    current_table.change_status(item, 'irrelevant')
    await call.answer(f'Уже не нужно:  {call.data[3:]} \U0001F44C', cache_time=1)
    actual_items_list = current_table.actual_items
    await request_manager(call, actual_items_list, state)


# Фоновая обработка удаления записи
# @dp.callback_query_handler(Text(startswith='DIF'), state=Step.wait_del_forever)
@dp.callback_query_handler(state=Step.wait_del_forever)
async def delete_forever(call: types.CallbackQuery, state: FSMContext):
    item = call.data
    current_table.delete_item(item)
    await call.answer(f'Удалено из записей: {call.data[3:]} \U0001F44C', cache_time=2)
    all_items_list = current_table.all_items
    await request_manager(call, all_items_list, state)


async def request_manager(request_type, current_list: list, state: FSMContext):
    """ Менеджер запросов """
    current_state = await state.get_state()
    print(current_state)
    answer = await get_answer_type(request_type)
    answer_txt = await get_answer_txt(current_list, current_state)
    markup = await get_markup(current_list, current_state)
    await answer(text=answer_txt, reply_markup=markup)


async def get_answer_type(request_type):
    """
    Возвращает тип ответа в зависимости от типа принятых данных (Message или CallbackQuery)
    """
    answer_func = None
    if isinstance(request_type, types.Message):
        answer_func = request_type.answer
    elif isinstance(request_type, types.CallbackQuery):
        answer_func = request_type.message.edit_text
    return answer_func


async def get_answer_txt(current_list, state):
    """
    Возвращает текст сообщения, зависимости от состояния FSM и наличия данных в текущем списке
    """

    if state == Step.wait_add_to_list.state:
        # сообщения для списка неактуальных записей
        if current_list:
            return 'Что нужно добавить? \U0001F914 '
        return 'Выбирать не из чего... \U00002639'
    if state == Step.wait_del_from_list.state:
        # сообщения для списка актуальных записей
        if current_list:
            return 'Вот список! \U0001F609 \n' f'Ред. в {current_table.updated_time}'
        return 'Список пуст! \U0001F389 '
    if state == Step.wait_del_forever.state:
        # сообщения для списка всех записей
        if current_list:
            return 'Что нужно удалить? \U0001F914 '
        return 'Удалять нечего! \U0001F923'


async def get_markup(current_list, state):
    """
    Возвращает разметку кнопок в зависимости от состояния FSM и наличия данных в текущем списке
    """
    global rows_count
    btn_list = list()
    if current_list:

        def get_btns(current_list):
            long_txt_flag = False
            btn_list = list()
            rows = int()
            for item in sorted(current_list):
                txt_size = sys.getsizeof(item)
                if txt_size > 100:
                    long_txt_flag = True
                if state == Step.wait_del_forever.state:
                    button_item = InlineKeyboardButton('\U0000274C  ' + item, callback_data=item)
                else:
                    button_item = InlineKeyboardButton(item, callback_data=item)
                btn_list.append(button_item)
            if long_txt_flag:
                rows = 1
            else:
                rows = 2
            return btn_list, rows

        btn_list, rows_count = get_btns(current_list)
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*btn_list)
    if state == Step.wait_add_to_list.state:
        markup.add(button_new)

    return markup


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(startswith='new_item'))
async def add_new(call: types.CallbackQuery):
    await call.message.edit_text('Просто напиши тут... \U0001F447')
    await call.answer()


@dp.message_handler(filter_users, commands='blocked')
async def show_blocked(message: types.Message):
    markup = InlineKeyboardMarkup()
    clear_btn = InlineKeyboardMarkup(text='Очистить список', callback_data='clear_blocked')
    markup.add(clear_btn)
    msg = ''
    for item in blocked_list.blocked:
        msg += f'id: {item[0]}  datetime: {item[1]}  message: {item[2]}\n'
    await message.answer(msg, reply_markup=markup)


@dp.callback_query_handler(Text(equals='clear_blocked'))
async def clear_blocked_list(call: types.CallbackQuery):
    blocked_list.clear()
    await call.answer(f'Список очищен! \U0001F44C', cache_time=2)
    await call.message.delete()


# Фоновая обработка текста новой записи
@dp.message_handler(filter_users)
async def add_new_item(message: types.Message):
    global current_table
    if current_table is None:
        return await start_chat(message)
    txt_size = sys.getsizeof(message.text)
    msg_txt = None
    if txt_size > 128:
        await message.answer(f'Слишком много слов! \n'
                             f'Давай покороче... \U0001F612')
    elif message.text not in current_table.all_items:
        current_table.add_new_item(message.text)
        msg_txt = f'Добавлено: {message.text} \U0001F44C '
    else:
        msg_txt = f'Не повторяйся! \U0000261D'
    await message.answer(msg_txt)


# Доп. функция. Формирует список кнопок из передаваемого множества


if __name__ == '__main__':
    executor.start_polling(dp)
