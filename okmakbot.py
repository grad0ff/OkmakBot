import logging
import sys

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, \
    InlineKeyboardButton
from aiogram.utils import executor

import config
from db_manage import TableManager, Blocked

ACTUAL = 'actual'
IRRELEVANT = 'irrelevant'
PRIORITY_1 = '\U00002780'
PRIORITY_2 = '\U00002781'

if sys.platform != 'win32':
    logging.basicConfig(filename=config.LOG_FILE, filemode='w')

storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

shopping_list = TableManager('product')
task_list = TableManager('task')
blocked_list = Blocked()
current_table = shopping_list

users = list(config.users.values())
rows_count = 2

btn_shopping = KeyboardButton('Покупки')
btn_tasks = KeyboardButton('Дела')
btn_add = KeyboardButton('Внести в список')
btn_show = KeyboardButton('Показать список')
btn_all = KeyboardButton('Показать всё')
btn_back = KeyboardButton('Выйти из')
btn_priority_1 = InlineKeyboardButton(PRIORITY_1, callback_data=PRIORITY_1)
btn_priority_2 = InlineKeyboardButton(PRIORITY_2, callback_data=PRIORITY_2)
btn_new = InlineKeyboardButton('НОВАЯ ЗАПИСЬ', callback_data='new')

menu_btns_txts = [btn_shopping.text, btn_tasks.text]
submenu_btns_txts = [btn_add.text, btn_show.text, btn_all.text, btn_back.text]
priority_btns_txts = [btn_priority_1.text, btn_priority_2.text]


class Step(StatesGroup):
    wait_current_list = State()
    wait_action = State()
    wait_priotity = State()
    wait_add_to_list = State()
    wait_del_from_list = State()
    wait_del_forever = State()
    wait_new_item = State()

    SUBMENU_STATES = [wait_add_to_list, wait_priotity, wait_del_from_list, wait_del_forever]


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
@dp.message_handler(Text(startswith=btn_back.text), state='*')
async def start_chat(message: types.Message, state: FSMContext):
    """
    Запускает бота и отображает основное меню
    """
    global current_table
    current_table = None
    markup = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Сначала выбери раздел!')
    markup.add(btn_shopping)
    markup.add(btn_tasks)
    await message.answer(f'Всегда готов! \U0001F44D \n'
                         'Выбери нужный раздел \U0001F4C2', reply_markup=markup)
    await state.finish()
    await Step.wait_current_list.set()


@dp.message_handler(commands='cancel', state='*')
async def cancel(message: types.Message, state: FSMContext):
    """
    Завершает чат и сбрасывает машину состояний
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Чат завершен!  \U000026D4", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(Text(equals=[btn_shopping.text, btn_tasks.text]), state=[Step.wait_current_list])
async def selected_current_list(message: types.Message, state: FSMContext):
    """
    Отображает пункты разделов, адаптирует текст кнопки выхода из раздела в соответствии с выбранным разделом
    """
    global current_table, rows_count
    msg_txt = message.text
    await state.update_data(current_list=msg_txt)
    if msg_txt == btn_shopping.text:
        current_table = shopping_list
        btn_back.text = 'Выйти из Покупок'
        rows_count = 2
    elif msg_txt == btn_tasks.text:
        current_table = task_list
        btn_back.text = 'Выйти из Дел'
        rows_count = 1
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_add, btn_show)
    markup.add(btn_all, btn_back)
    await message.answer('Выбери действие \U000027A1', reply_markup=markup)
    await Step.wait_action.set()


@dp.message_handler(Text(equals=submenu_btns_txts), state=[Step.wait_action, *Step.SUBMENU_STATES])
async def selected_action(message: types.Message, state: FSMContext):
    """
    Отображает перечень действий, доступных для текущего списка
    """
    await state.update_data(action=message.text)
    items_list = list()
    msg_txt = message.text
    if msg_txt == btn_add.text:
        items_list = current_table.get_items(IRRELEVANT)
        await Step.wait_add_to_list.set()
    if msg_txt == btn_show.text:
        items_list = current_table.get_items(ACTUAL)
        await Step.wait_del_from_list.set()
    if msg_txt == btn_all.text:
        items_list = current_table.get_all_items()
        await Step.wait_del_forever.set()
    await answer_manager(message, items_list, state)


@dp.message_handler(state=Step.wait_new_item)
@dp.callback_query_handler(lambda call: call.data != btn_new.callback_data, state=Step.wait_add_to_list)
async def add_to_list(call: types.CallbackQuery, state: FSMContext):
    """
    Фоновая обработка добавления записи из неактуального списка в актуальный, включая изменение статуса в БД
    """
    item = str()
    func = None
    if isinstance(call, types.CallbackQuery):
        item = call.data
        func = call.message.edit_text
        await func(f'Нужно:  {item} \U0001F44C')
    elif isinstance(call, types.Message):
        item = call.text
        func = call.answer
    await state.update_data(item=item)
    current_table.change_status(item, status=ACTUAL)
    markup = InlineKeyboardMarkup()
    markup.add(btn_priority_1, btn_priority_2)
    await func('Выбери приоритет \U000027A1', reply_markup=markup)
    await Step.wait_priotity.set()


@dp.callback_query_handler(state=Step.wait_priotity)
async def get_priority(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = data.get('item')
    priority = call.data
    current_table.change_priority(item, priority=priority)
    irrelevant_items_list = current_table.get_items(IRRELEVANT)
    await Step.wait_add_to_list.set()
    await answer_manager(call, irrelevant_items_list, state)


@dp.callback_query_handler(state=Step.wait_del_from_list)
async def show_list(call: types.CallbackQuery, state: FSMContext):
    """
    Фоновая обработка переноса записи из актуального списка в неактуальный, включая изменение статуса в БД
    """
    item = call.data
    current_table.change_status(item, IRRELEVANT)
    await call.answer(f'Уже не нужно:  {item} \U0001F44C', cache_time=1)
    actual_items_list = current_table.get_items(ACTUAL)
    await answer_manager(call, actual_items_list, state)


@dp.callback_query_handler(state=Step.wait_del_forever)
async def delete_forever(call: types.CallbackQuery, state: FSMContext):
    """
    Фоновая обработка удаления записи из полного списка и БД

    """
    item = call.data
    current_table.delete_item(item)
    await call.answer(f'Удалено из записей: {item} \U0001F44C', cache_time=2)
    all_items_list = current_table.get_all_items()
    await answer_manager(call, all_items_list, state)


async def answer_manager(request_type, current_list: list, state: FSMContext):
    """
    Менеджер запросов, обрабатывает типы Message и CallbackQuery
    """
    current_state = await state.get_state()
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


async def get_answer_txt(current_list, state: str) -> str:
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
        long_txt_flag = False
        for item in sorted(current_list):
            txt_size = sys.getsizeof(item)
            if txt_size > 100:
                long_txt_flag = True
            button_item = InlineKeyboardButton(item, callback_data=item)
            if state == Step.wait_del_forever.state:
                button_item.text = '\U0000274C  ' + button_item.text
            btn_list.append(button_item)
        if long_txt_flag:
            rows_count = 1
        else:
            rows_count = 2
    markup = InlineKeyboardMarkup(row_width=rows_count)
    markup.add(*btn_list)
    if state == Step.wait_add_to_list.state:
        markup.add(btn_new)

    return markup


# Фоновая обработка кнопки добавления новой записи
@dp.callback_query_handler(Text(equals='new'), state=Step.wait_add_to_list)
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
@dp.message_handler(filter_users, state='*')
async def add_new_item(message: types.Message, state: FSMContext):
    global current_table
    msg_txt = message.text
    if await state.get_state() == Step.wait_current_list.state:
        return await message.answer('Сначала выбери нужный раздел! \U0001F4C2')
    txt_size = sys.getsizeof(msg_txt)
    if txt_size > 128:
        return await message.answer(f'Слишком много слов! \n'
                                    f'Давай покороче... \U0001F612')
    if msg_txt not in current_table.get_all_items():
        await Step.wait_add_to_list.set()
        await add_to_list(msg_txt, state)
        # current_table.add_new_item(new_item)
        # msg_txt = f'Добавлено: {message.text} \U0001F44C '
    else:
        msg_txt = f'Не повторяйся! \U0000261D'
    await message.answer(msg_txt)


# Доп. функция. Формирует список кнопок из передаваемого множества


if __name__ == '__main__':
    executor.start_polling(dp)
