import sqlite3

import config
from app_exceptions import TableNameError
from services import Services

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class TableManager:
    """
    Базовый клас для списков, нпр списка покупок или списка дел, определяемых как дочерние классы
    Base class for lists, s.a. shopping lists or task lists defined as subclusses
    """

    def __init__(self, table_name: str) -> None:
        self.__list_actual = list()
        self.__list_irrelevant = list()
        self.__list_all = list()
        self.__updated_time = str()
        self.__item = 'item'
        self.__status = 'status'
        self.__priority = 'priority'
        if isinstance(table_name, str):
            self.__table_name = table_name
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.__table_name} (item VARCHAR(32), "
                           f"status VARCHAR(16), priority INTEGER)"
                           )
        else:
            raise TableNameError

    @property
    def table_name(self):
        return self.__table_name

    def get_items(self, status: str) -> list:
        __list_priority_1 = list(
            map(lambda x: x[0], cursor.execute(
                f"SELECT item FROM {self.table_name} WHERE status = '{status}' AND priority = 1").fetchall()
                )
        )
        __list_priority_2 = list(
            map(lambda x: x[0], cursor.execute(
                f"SELECT item FROM {self.table_name} WHERE status = '{status}' AND priority = 2").fetchall()
                )
        )

        return [__list_priority_1, __list_priority_2]

    def get_all_items(self) -> list:
        __list_all = list(map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.table_name}').fetchall()))
        return __list_all

    def change_status(self, item: str, status: str, priority: int = 2) -> None:
        """
        Меняет актуальность записи
        """
        cursor.execute(
            f"UPDATE {self.table_name} SET status = '{status}', priority = {priority} WHERE item = '{item}'"
        )
        self.set_timestamp()
        connection.commit()

    def insert_new_item(self, item: str) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        cursor.execute(f"INSERT INTO {self.table_name} VALUES ('{item}', '', 1)")
        connection.commit()

    def delete_item(self, item: str) -> None:
        """
        Удаляет товар из БД
        """
        cursor.execute(f"DELETE FROM {self.__table_name} WHERE item = '{item}'")
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
