import sqlite3
import pytz

from datetime import datetime

connection = sqlite3.connect('bot_db.db')
with connection:
    cursor = connection.cursor()

tz_Moscow = pytz.timezone('Europe/Moscow')


class ShoppingList:
    def __init__(self):
        cursor.execute("CREATE TABLE IF NOT EXISTS products (item TEXT, status TEXT)")
        self.update_data()
        self.edit_datetime = None

    # обновить все списки
    def update_data(self):
        self.products = list(
            map(lambda x: x[0], cursor.execute("SELECT item FROM products").fetchall())
        )
        self.shoplist = list(
            map(lambda x: x[0], cursor.execute("SELECT item FROM products WHERE status = 'to purchase'").fetchall())
        )
        self.not_purchased_list = list(
            map(lambda x: x[0], cursor.execute("SELECT item FROM products WHERE status = 'not purchased'").fetchall())
        )
        self.edit_datetime = datetime.now(tz_Moscow).strftime('%H:%M: %d.%m.%y')

    # добавить товар в список покупок
    def add_to_shoplist(self, item):
        cursor.execute(f"UPDATE products SET status = 'to purchase' WHERE item = {item}")
        connection.commit()
        print('Добавлено в список: ', item)
        self.update_data()

    # удалить товар из списка покупок
    def del_from_shoplist(self, item):
        cursor.execute(f"UPDATE products SET status = 'not purchased' WHERE item = {item}")
        self.shoplist.remove(item)
        self.update_data()
        print('Удалено из списка: ', item)

    # довать новый товар
    def add_new_item(self, item):
        if item not in self.products:
            cursor.execute(f"INSERT INTO products VALUES ({item}, 'to purchase')")
        connection.commit()
        self.update_data()
        print('Добавлено в список и записи: ', item)

    # удалить товар из БД
    def delete_item(self, item):
        cursor.execute(f"DELETE FROM products WHERE item = {item}")
        connection.commit()
        print('Удалено из записей: ', item)
        self.update_data()

    def get_all_items(self):
        return self.products
