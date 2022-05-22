import sqlite3
from sqlite3 import Cursor

import config

from services import Services

# with sqlite3.connect(config.DATABASE) as connection:
#     cursor = connection.cursor()

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class TableNameError(Exception):
    pass


class Table:
    """
    Базовый клас для списков, нпр списка покупок или списка дел, определяемых как дочерние классы
    Base class for lists, s.a. shopping lists or task lists defined as subclusses
    """
    __actual_list = list()
    __irrelevant_list = list()
    __all_items = list()
    updated_time = str()

    def __init__(self, table_name: str) -> None:
        if isinstance(table_name, str):
            self.__table_name = table_name
            cursor.execute(
                f'CREATE TABLE IF NOT EXISTS {self.__table_name} (item VARCHAR(32), status VARCHAR(32), '
                f'priority VARCHAR(16))'
            )
        else:
            raise TableNameError

    @property
    def table_name(self):
        return self.__table_name

    @property
    def actual_items(self) -> list:
        list_of_actual = list(
            map(lambda x: x[0],
                cursor.execute(f'SELECT item FROM {self.__table_name} WHERE status = "actual"').fetchall())
        )
        return list_of_actual

    @property
    def irrelevant_items(self) -> list:
        list_of_irrelevant = list(
            map(lambda x: x[0],
                cursor.execute(f'SELECT item FROM {self.__table_name} WHERE status = "irrelevant"').fetchall())
        )
        return list_of_irrelevant

    @property
    def all_items(self) -> list:
        list_of_all = list(map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.__table_name}').fetchall()))
        return list_of_all

    def change_status(self, item: str, status: str) -> None:
        """
        Меняет состояние сущности из неактуального на актульное и наоборот
        """
        cursor.execute(f'UPDATE {self.__table_name} SET status = "{status}" WHERE item = "{item}"')
        self.set_timestamp()
        connection.commit()

    def add_new_item(self, new_item: str) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        if new_item not in self.all_items:
            cursor.execute(f'INSERT INTO {self.__table_name} VALUES ("{new_item}", "actual")')
        self.set_timestamp()
        connection.commit()

    def delete_item(self, item: str) -> None:
        """
        Удаляет товар из БД
        """
        cursor.execute(f'DELETE FROM {self.__table_name} WHERE item = "{item}"')
        connection.commit()

    @classmethod
    def set_timestamp(self) -> None:
        self.updated_time = Services.get_datetime()


class Blocked():
    __table_name = 'blocked'

    def __init__(self):
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.__table_name} (user_id INTEGER, datetime TEXT, msg TEXT)')

    def add(self, user_id: int, msg: str) -> None:
        cursor.execute(f'INSERT INTO {self.__table_name} VALUES ({user_id}, {Services.get_datetime()}, {repr(msg)})')
        connection.commit()

    @property
    def blocked(self) -> list:
        blocked = cursor.execute(f'SELECT * FROM {self.__table_name}').fetchall()
        return blocked

    def clear(self) -> None:
        cursor.execute(f'DELETE FROM {self.__table_name}')
        connection.commit()
