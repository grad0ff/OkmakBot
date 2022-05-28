from aiogram.types import KeyboardButton, InlineKeyboardButton

btn_shopping = KeyboardButton('Покупки')
btn_tasks = KeyboardButton('Дела')
btn_add = KeyboardButton('Внести в список')
btn_show = KeyboardButton('Показать список')
btn_all = KeyboardButton('Показать всё')
btn_back = KeyboardButton('Выйти из')

btn_yes = InlineKeyboardButton('Да', callback_data='YES')
btn_no = InlineKeyboardButton('Нет', callback_data='NO')

menu_btn_txt = [btn_shopping.text, btn_tasks.text]
submenu_btn_txt = [btn_add.text, btn_show.text, btn_all.text, btn_back.text]
yn_btn_data = [btn_yes.callback_data, btn_no.callback_data]