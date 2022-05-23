import sqlite3

import config
from services import Services

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class TableNameError(Exception):
    pass


class TableManager:
    """
    Базовый клас для списков, нпр списка покупок или списка дел, определяемых как дочерние классы
    Base class for lists, s.a. shopping lists or task lists defined as subclusses
    """

    def __init__(self, table_name: str) -> None:
        self.__list_of_actual = list()
        self.__list_of_irrelevant = list()
        self.__list_of_all = list()
        self.__updated_time = str()
        self.__item = 'item'
        self.__status = 'status'
        self.__priority = 'priority'
        if isinstance(table_name, str):
            self.__table_name = table_name
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.__table_name} (item VARCHAR(32), "
                           f"status VARCHAR(32), priority VARCHAR(16))"
                           )
        else:
            raise TableNameError

    @property
    def table_name(self):
        return self.__table_name

    def get_items(self, status: str) -> list:
        __list_of_items = list(
            map(lambda x: x[0],
                cursor.execute(f"SELECT item FROM {self.table_name} WHERE status = '{status}'").fetchall())
        )
        return __list_of_items

    def get_all_items(self) -> list:
        __list_of_all = list(map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.table_name}').fetchall()))
        return __list_of_all

    def change_status(self, item_name: str, status: str) -> None:
        """
        Меняет актуальность записи
        """
        cursor.execute(
            f"UPDATE {self.table_name} SET status = '{status}' WHERE item = '{item_name}'"
        )
        self.set_timestamp()
        connection.commit()

    def change_priority(self, item_name: str, priority: str):
        """
        Меняет приоритет записи
        """
        cursor.execute(
            f"UPDATE {self.table_name} SET priority = '{priority}' WHERE item = '{item_name}'"
        )
        self.set_timestamp()
        connection.commit()

    def add_new_item(self, item_name: str, status: str) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        cursor.execute(f"INSERT INTO {self.table_name} VALUES ('{item_name}', '{status}')")
        self.set_timestamp()
        connection.commit()

    def delete_item(self, item_name: str) -> None:
        """
        Удаляет товар из БД
        """
        cursor.execute(f"DELETE FROM {self.__table_name} WHERE item = '{item_name}'")
        connection.commit()

    def set_timestamp(self) -> None:
        self.__updated_time = Services.get_datetime()

    @property
    def updated_time(self):
        return self.__updated_time


class Blocked():
    __table_name = 'blocked'

    def __init__(self):
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.__table_name} (user_id INTEGER, datetime TEXT, msg TEXT)')

    def add(self, user_id: int, msg: str) -> None:
        cursor.execute(f'INSERT INTO {self.__table_name} VALUES ("{user_id}", '
                       f'"{Services.get_datetime()}", "{repr(msg)}")')
        connection.commit()

    @property
    def blocked(self) -> list:
        blocked = cursor.execute(f'SELECT * FROM {self.__table_name}').fetchall()
        return blocked

    def clear(self) -> None:
        cursor.execute(f'DELETE FROM {self.__table_name}')
        connection.commit()
