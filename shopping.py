import sqlite3
import pytz

from datetime import datetime

connection = sqlite3.connect('bot_db.db')
cursor = connection.cursor()

tz_Moscow = pytz.timezone('Europe/Moscow')


class ShoppingList:
    COUNT = 0

    def __init__(self):
        cursor.execute("CREATE TABLE IF NOT EXISTS products (item, status)")
        self.products = cursor.execute("SELECT item FROM products").fetchall()
        self.shoplist = cursor.execute("SELECT item FROM products WHERE status = 'to purchase'").fetchall()
        self.not_purchased_list = cursor.execute("SELECT item FROM products WHERE status = 'not purchased'").fetchall()
        self.edit_datetime = None
        ShoppingList.COUNT += 1

    def update_data(self):
        pass
        # self.not_purchased_list = self.products.difference(self.shoplist)
        # self.edit_datetime = datetime.now(tz_Moscow).strftime('%H:%M:%S %d.%m.')

    def add_to_shoplist(self, item):
        cursor.execute(f"UPDATE products SET status = 'to purchase' WHERE item = {item}")
        print('Добавлено в список: ', item)
        self.update_data()

    def del_from_shoplist(self, item):
        cursor.execute(f"DELETE FROM products
        self.shoplist.remove(item)
        self.update_data()
        print('Удалено из списка: ', item)

    def add_new_item(self, new_item):
        cursor.execute(f"INSERT INTO products VALUES ({new_item}, 'to purchase')")
        # self.add_to_shoplist(new_item)
        self.update_data()
        print('Добавлено в список и записи: ', new_item)

    def delete_item(self, item):
        self.products.remove(item)
        if item in self.shoplist:
            self.shoplist.remove(item)
            print('Удалено из записей: ', item)
        self.update_data()

    def get_all_items(self):
        return self.products
