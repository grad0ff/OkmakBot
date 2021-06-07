import telebot, time, logging
from telebot import types

bot = telebot.TeleBot("1825854132:AAFn3pRQ7yhRemHc5cSsG_e3MohAyC9lQyA")


class ShoppingList:
    COUNT = 0
    __PRODUCTS = {'A', 'B', 'C', 'D', 'E', 'F'}

    def __init__(self):
        self.shoplist = set()
        self.not_added_list = ShoppingList.__PRODUCTS
        ShoppingList.COUNT += 1

    def add_to_shoplist(self, item):
        self.shoplist.add(item)
        self.not_added_list = ShoppingList.__PRODUCTS.difference(self.shoplist)
        print('В списке: ', self.shoplist)
        print('Не в списке: ', self.not_added_list)

    def del_from_shoplist(self, item):
        self.shoplist.remove(item)
        self.not_added_list = ShoppingList.__PRODUCTS.difference(self.shoplist)
        print('Удалено: ', item)

    def add_new_item(self, new_item):
        ShoppingList.__PRODUCTS.add(new_item)

    def delete_item(self, item):
        ShoppingList.__PRODUCTS.remove(item)

    def get_all_items(self):
        return ShoppingList.__PRODUCTS


shopping_list = ShoppingList()


# запустить Telegram бот
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Купить', 'Список')
    markup.row('Полный список')

    bot.send_message(message.chat.id, 'Слушаю внимательно!', reply_markup=markup)


# Показать список покупок
@bot.message_handler(regexp='Список')
def get_shopping_list(message):
    if shopping_list.shoplist:
        markup = types.InlineKeyboardMarkup()
        markup.row(*display_btns(shopping_list.shoplist))
        bot.send_message(message.chat.id, 'Вот список покупок:', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Список покупок пуст! 😁')


# Добавить товар в список
@bot.message_handler(regexp='Купить')
def to_buy(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(*display_btns(shopping_list.not_added_list))
    button_new = types.InlineKeyboardButton('Новое', callback_data='new_item')
    markup.row(button_new)
    bot.send_message(message.chat.id, 'Что же нужно купить? 🤔', reply_markup=markup)


# Показать все продукты
@bot.message_handler(regexp='Полный список')
def show_all_list(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(*display_btns(shopping_list.get_all_items()))
    bot.send_message(message.chat.id, 'Все продукты:', reply_markup=markup)


# Фоновая обработка запросов
@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    if call.data == 'new_item':
        print('new_item')
        bot.send_message(call.message.chat.id, f'Что вносим?')


        # new_item = bot.
        # shopping_list.add_new_item(new_item)
        # bot.answer_callback_query(callback_query_id= call.id, text=f'Добавлено в перечень:   {str(call.data)}')

    elif call.data not in shopping_list.shoplist:
        shopping_list.add_to_shoplist(call.data)
        bot.answer_callback_query(callback_query_id= call.id, text=f'Добавлено в список:   {str(call.data)}')
        # time.sleep(2)
        to_buy(call.message)
    elif call.data in shopping_list.shoplist:
        shopping_list.del_from_shoplist(call.data)
        bot.answer_callback_query(callback_query_id= call.id, text=f'Удалено из списка:   {str(call.data)}')
        # time.sleep(2)
        get_shopping_list(call.message)
    if call.data in shopping_list.get_all_items():
        shopping_list.delete_item(call.data)
        print(shopping_list.get_all_items())
    bot.answer_callback_query(call.id)


# Формирует список из множества
def display_btns(list_type):
    btn_list = []
    for item in sorted(list_type):
        button_item = types.InlineKeyboardButton(item, callback_data=item)
        btn_list.append(button_item)
    return btn_list


bot.polling()
