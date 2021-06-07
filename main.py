import telebot, time
from telebot import types

bot = telebot.TeleBot("1825854132:AAFn3pRQ7yhRemHc5cSsG_e3MohAyC9lQyA")


class ShoppingList:
    COUNT = 0
    PRODUCTS = {'A', 'B', 'C', 'D', 'E', 'F'}

    def __init__(self):
        self.shoplist = set()
        self.not_added_list = ShoppingList.PRODUCTS
        ShoppingList.COUNT += 1

    def add_item(self, item):
        self.shoplist.add(item)
        self.not_added_list = ShoppingList.PRODUCTS.difference(self.shoplist)
        print('В списке: ', self.shoplist)
        print('Не в списке: ', self.not_added_list)

    def del_item(self):
        pass

    def purchased(self):
        pass


shopping_list = ShoppingList()


# запуск бота
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton('/Купить')
    button_2 = types.KeyboardButton('/Список')
    markup.row(button_1, button_2)
    bot.send_message(message.chat.id, 'Слушаю внимательно!', reply_markup=markup)


# отображение списка покупок
@bot.message_handler(commands=['Список'])
def get_shopping_list(message):
    if shopping_list.shoplist:
        markup = types.InlineKeyboardMarkup()
        markup.row(*display_btns(shopping_list.shoplist))
        bot.send_message(message.chat.id, 'Вот список:', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Список пуст! 😁')


# отображение позиций вне списка покупок
# @bot.callback_query_handler(func=get_shopping_list)
# def handle(call):
#     shopping_list.add_item(call.data)
#     bot.send_message(call.message.chat.id, f'Удалено из списка:   {str(call.data)}')
#     to_buy(call.message)
#     bot.answer_callback_query(call.id)
#
#     bot.send_message(message.chat.id, shopping_list.get_list())


# добавление товара в список покупок
@bot.message_handler(commands=['Купить'])
def to_buy(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(*display_btns(shopping_list.not_added_list))
    button_new = types.InlineKeyboardButton('Новое', callback_data='c')
    markup.row(button_new)
    bot.send_message(message.chat.id, 'Что же нужно купить? 🤔', reply_markup=markup)


# отображение позиций вне списка покупок
@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    shopping_list.add_item(call.data)
    bot.send_message(call.message.chat.id, f'Добавлено в список:   {str(call.data)} 👍')
    bot.answer_callback_query(call.id)
    time.sleep(1)
    to_buy(call.message)


# Доп. функция. Отображение кол-ва кнопок в зависимости от типа списка
def display_btns(list_type):
    btn_list = []
    for item in sorted(list_type):
        button_item = types.InlineKeyboardButton(item, callback_data=item)
        btn_list.append(button_item)
    return btn_list




bot.polling()
