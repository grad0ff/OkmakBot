import sqlite3
import config

from services import Services

connection = sqlite3.connect(config.db_path)
with connection:
    cursor = connection.cursor()


class Main:
    def __init__(self, table_name):
        self.table_name = table_name
        # cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (item TEXT, status TEXT)")
        self._actual_list = self._notactual_list = self._all_items = self.updated_datetime = None
        # self.update_data()

    # обновить все списки
    def update_data(self):
        self.get_actual_list()
        self.get_notactual_list()
        self.get_all_list()
        self.updated_datetime = Services.get_datetime()

    def get_all_list(self):
        all_items = list(
            map(lambda x: x[0], cursor.execute(f"SELECT item FROM {self.table_name}").fetchall())
        )
        return all_items

    def get_notactual_list(self):
        notactual_list = list(
            map(lambda x: x[0],
                cursor.execute(f"SELECT item FROM {self.table_name} WHERE status = 'not_actual'").fetchall())
        )
        return notactual_list

    def get_actual_list(self):
        actual_list = list(
            map(lambda x: x[0],
                cursor.execute(f"SELECT item FROM {self.table_name} WHERE status = 'actual'").fetchall()))
        return actual_list

    # добавить товар в список покупок
    def add_to_shoplist(self, item):
        cursor.execute(f"UPDATE {self.table_name} SET status = 'actual' WHERE item = '{item}'")
        connection.commit()
        self.update_data()

    # удалить товар из списка покупок
    def del_from_shoplist(self, item):
        cursor.execute(f"UPDATE {self.table_name} SET status = 'not_actual' WHERE item = '{item}'")
        # self.get_actual_list().remove(item)
        self.update_data()

    # добавить новый товар
    def add_new_item(self, item):
        if item not in self.get_all_list():
            cursor.execute(f"INSERT INTO {self.table_name} VALUES ('{item}', 'actual')")
        connection.commit()
        self.update_data()

    # удалить товар из БД
    def delete_item(self, item):
        cursor.execute(f"DELETE FROM {self.table_name} WHERE item = '{item}'")
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
        cursor.execute("CREATE TABLE IF NOT EXISTS blocked_users (userID INTEGER, datetime TEXT, msg_text TEXT)")

    @staticmethod
    def set_blocked_id(user_id, text):
        cursor.execute(f"INSERT INTO blocked_users VALUES ({user_id}, {Services.get_datetime()}, {repr(text)})")
        connection.commit()

    @staticmethod
    def get_blocked():
        blocked_list = cursor.execute(f"SELECT * FROM blocked_users").fetchall()
        return blocked_list

    @staticmethod
    def clear_list():
        cursor.execute("DELETE FROM blocked_users")
        connection.commit()
