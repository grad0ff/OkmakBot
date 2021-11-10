import sqlite3
import pytz

from datetime import datetime

# connection = sqlite3.connect('/dir/okmak_data/bot_db.db')
connection = sqlite3.connect('bot_db.db')

with connection:
    cursor = connection.cursor()


class Main:
    def __init__(self, table_name):
        self.table_name = table_name
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (item TEXT, status TEXT)")
        self.update_data()

    # обновить все списки
    def update_data(self):
        self.all_items = list(
            map(lambda x: x[0], cursor.execute(f"SELECT item FROM {self.table_name}").fetchall())
        )
        self.actual_list = list(
            map(lambda x: x[0],
                cursor.execute(f"SELECT item FROM {self.table_name} WHERE status = 'actual'").fetchall())
        )
        self.not_in_actual_list = list(
            map(lambda x: x[0],
                cursor.execute(f"SELECT item FROM {self.table_name} WHERE status = 'not_actual'").fetchall())
        )
        self.datetime = get_datetime()

    # добавить товар в список покупок
    def add_to_shoplist(self, item):
        cursor.execute(f"UPDATE {self.table_name} SET status = 'actual' WHERE item = {item}")
        connection.commit()
        self.update_data()

    # удалить товар из списка покупок
    def del_from_shoplist(self, item):
        cursor.execute(f"UPDATE {self.table_name} SET status = 'not_actual' WHERE item = {item}")
        self.actual_list.remove(item)
        self.update_data()

    # добавить новый товар
    def add_new_item(self, item):
        if item not in self.all_items:
            cursor.execute(f"INSERT INTO {self.table_name} VALUES ('{item}', 'actual')")
        connection.commit()
        self.update_data()

    # удалить товар из БД
    def delete_item(self, item):
        cursor.execute(f"DELETE FROM {self.table_name} WHERE item = {item}")
        connection.commit()
        self.update_data()


class ShoppingList(Main):
    TABLE_NAME = 'product_table'

    def __init__(self):
        super().__init__(self.TABLE_NAME)


class ToDoList(Main):
    TABLE_NAME = 'todo_table'

    def __init__(self):
        super().__init__(self.TABLE_NAME)


class BlockedUsers():
    def __init__(self):
        cursor.execute("CREATE TABLE IF NOT EXISTS blocked_users (userID INTEGER, datetime, msg_text)")

    def set_blocked_id(self, user_id, text):
        cursor.execute(f"INSERT INTO blocked_users VALUES ({user_id}, {get_datetime()}, {text})")
        connection.commit()

    def get_blocked(self):
        self.blocked_id_list = list(
            map(lambda x: x[0], cursor.execute(f"SELECT * FROM blocked_users").fetchall())
        )


def get_datetime():
    tz_Moscow = pytz.timezone('Europe/Moscow')
    return datetime.now(tz_Moscow).strftime('%H:%M %d.%m.%y')
