import sqlite3
import pytz

from datetime import datetime

connection = sqlite3.connect('/dir/okmak_data/bot_db.db')
with connection:
    cursor = connection.cursor()


class ShoppingList:
    def __init__(self):
        cursor.execute("CREATE TABLE IF NOT EXISTS products (item TEXT, status TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS blocked (userID INTEGER, datetaime, text)")
        self.update_data()

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
        self.blocked_id_list = list(
            map(lambda x: x[0], cursor.execute("SELECT userID FROM blocked").fetchall())
        )
        self.datetime = get_datetime()

    # добавить товар в список покупок
    def add_to_shoplist(self, item):
        cursor.execute(f"UPDATE products SET status = 'to purchase' WHERE item = '{item}'")
        connection.commit()
        self.update_data()

    # удалить товар из списка покупок
    def del_from_shoplist(self, item):
        cursor.execute(f"UPDATE products SET status = 'not purchased' WHERE item = '{item}'")
        self.shoplist.remove(item)
        self.update_data()

    # довать новый товар
    def add_new_item(self, item):
        if item not in self.products:
            cursor.execute(f"INSERT INTO products VALUES ('{item}', 'to purchase')")
        connection.commit()
        self.update_data()

    # удалить товар из БД
    def delete_item(self, item):
        cursor.execute(f"DELETE FROM products WHERE item = '{item}'")
        connection.commit()
        self.update_data()


def set_blocked_id(user_id, text):
    cursor.execute(f"INSERT INTO blocked VALUES ({user_id}, '{get_datetime()}', '{text}')")
    connection.commit()


def get_datetime():
    tz_Moscow = pytz.timezone('Europe/Moscow')
    return datetime.now(tz_Moscow).strftime('%H:%M %d.%m.%y')
