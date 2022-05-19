import sqlite3
from sqlite3 import Cursor

import config

from services import Services

# with sqlite3.connect(config.DATABASE) as connection:
#     cursor = connection.cursor()

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class Base:
    __actual_list = []
    __irrelevant_list = []
    __all_items = []
    updated_time = ''

    def __init__(self, table_name: str) -> None:
        self.__table = table_name
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.__table} (item VARCHAR(32), status VARCHAR(32))')

    @property
    def all_items(self) -> list:
        list_of_all = list(map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.__table}').fetchall()))
        return list_of_all

    @property
    def irrelevant_items(self) -> list:
        list_of_irrelevant = list(
            map(lambda x: x[0],
                cursor.execute(f'SELECT item FROM {self.__table} WHERE status = "irrelevant"').fetchall())
        )
        return list_of_irrelevant

    @property
    def actual_items(self) -> list:
        list_of_actual = list(
            map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.__table} WHERE status = "actual"').fetchall())
        )
        return list_of_actual

    def set_actual(self, item: str) -> None:
        """
        Меняет состояние сущности из неактуального на актульное
        """
        cursor.execute(f'UPDATE {self.__table} SET status = "actual" WHERE item = "{item}"')
        self.set_timestamp()
        connection.commit()

    def set_irrelevant(self, item: str) -> None:
        """
        Меняет состояние сущности из актуалнього на неактульное
        """
        cursor.execute(f'UPDATE {self.__table} SET status = "irrelevant" WHERE item = "{item}"')
        self.set_timestamp()
        connection.commit()

    def add_new_item(self, new_item: str) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        if new_item not in self.all_items:
            cursor.execute(f'INSERT INTO {self.__table} VALUES ("{new_item}", "actual")')
        self.set_timestamp()
        connection.commit()

    def delete_item(self, item: str) -> None:
        """
        Удалаяет товар из БД
        """
        cursor.execute(f'DELETE FROM {self.__table} WHERE item = "{item}"')
        connection.commit()

    @classmethod
    def set_timestamp(self) -> None:
        self.updated_time = Services.get_datetime()


class Shopping(Base):
    __table_name = 'product'

    def __init__(self):
        super().__init__(self.__table_name)


class ToDo(Base):
    __table_name = 'todo'

    def __init__(self):
        super().__init__(self.__table_name)


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
