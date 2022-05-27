from aiogram.dispatcher.filters.state import StatesGroup, State


class AppState(StatesGroup):
    wait_current_list = State()
    wait_action = State()
    wait_add_to_list = State()
    wait_priority = State()
    wait_priority_new = State()
    wait_del_from_list = State()
    wait_del_forever = State()
    wait_new_item = State()

    submenu_states = [wait_add_to_list, wait_priority, wait_del_from_list, wait_del_forever]