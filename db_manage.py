import sqlite3

import config
from app_exceptions import TableNameError
from services import Services

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class BaseList:
    """
    Базовый клас для списков, нпр списка покупок или списка дел, определяемых как дочерние классы
    Base class for lists, s.a. shopping lists or task lists defined as subclusses
    """

    def __init__(self, table_name: str):
        self.__list_actual = list()
        self.__list_irrelevant = list()
        self.__list_all = list()
        self.__updated_time = str()
        self.__ITEM = 'item'
        self.__STATUS = 'status'
        self.__PRIORITY = 'priority'
        self.__ACTUAL = 'actual'
        self.__IRRELEVANT = 'irrelevant'
        if isinstance(table_name, str):
            self.__table_name = table_name
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} "
                           f"({self.__ITEM} VARCHAR(32), "
                           f"{self.__STATUS} VARCHAR(16), "
                           f"{self.__PRIORITY} INTEGER)"
                           )
        else:
            raise TableNameError

    @property
    def table_name(self):
        return self.__table_name

    @staticmethod
    def list_converter(iterable):
        return list(map(lambda x: x[0], iterable))

    @property
    def actual_items(self) -> list:

        __list_priority_1 = self.list_converter(cursor.execute(
            f"SELECT {self.__ITEM} FROM {self.table_name} "
            f"WHERE {self.__STATUS} = '{self.__ACTUAL}' AND {self.__PRIORITY} = 1 "
            f"ORDER BY {self.__ITEM}"
        ).fetchall())

        __list_priority_2 = self.list_converter(cursor.execute(
            f"SELECT {self.__ITEM} FROM {self.table_name} "
            f"WHERE {self.__STATUS} = '{self.__ACTUAL}' AND {self.__PRIORITY} = 2 "
            f"ORDER BY {self.__ITEM}"
        ).fetchall())

        return [__list_priority_1, __list_priority_2]

    @property
    def irrelevant_items(self) -> list:
        __list_irrelevant = self.list_converter(cursor.execute(
            f"SELECT {self.__ITEM} FROM {self.table_name} "
            f"WHERE {self.__STATUS} = '{self.__IRRELEVANT}'"
            f"ORDER BY {self.__ITEM}"
        ).fetchall())
        return __list_irrelevant

    @property
    def all_items(self) -> list:
        __list_all = self.list_converter(cursor.execute(
            f'SELECT {self.__ITEM} FROM {self.table_name}'
        ).fetchall())
        return __list_all

    def set_actual(self, item: str, priority: int = 2) -> None:
        """
        Меняет актуальность записи на актуальный
        """
        cursor.execute(
            f"UPDATE {self.table_name} SET "
            f"{self.__STATUS} = '{self.__ACTUAL}', "
            f"{self.__PRIORITY} = {priority} "
            f"WHERE {self.__ITEM} = '{item}'"
        )
        self.set_timestamp()
        connection.commit()

    def set_irrelevant(self, item: str) -> None:
        """
        Меняет актуальность записи на неактуальный
        """
        cursor.execute(
            f"UPDATE {self.table_name} SET "
            f"{self.__STATUS} = '{self.__IRRELEVANT}' "
            f"WHERE {self.__ITEM} = '{item}'"
        )
        self.set_timestamp()
        connection.commit()

    def insert_new_item(self, item: str) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        cursor.execute(
            f"INSERT INTO {self.table_name} "
            f"VALUES ('{item}', '', 1)"
        )
        connection.commit()

    def delete_item(self, item: str) -> None:
        """
        Удаляет товар из БД
        """
        cursor.execute(
            f"DELETE FROM {self.__table_name} "
            f"WHERE {self.__ITEM} = '{item}'"
        )
        connection.commit()

    def set_timestamp(self) -> None:
        self.__updated_time = Services.get_datetime()

    @property
    def updated_time(self):
        return self.__updated_time


class Blocked():

    def __init__(self, table_name):
        if isinstance(table_name, str):
            self.__table_name = table_name
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} (user_id INTEGER, datetime TEXT, msg TEXT)")

    @property
    def table_name(self):
        return self.__table_name

    def add(self, user_id: int, msg: str) -> None:
        cursor.execute(f"INSERT INTO {self.table_name} VALUES ('{user_id}', "
                       f"'{Services.get_datetime()}', '{repr(msg)}')")
        connection.commit()

    @property
    def blocked(self) -> list:
        blocked = cursor.execute(f"SELECT * FROM {self.table_name}").fetchall()
        return blocked

    def clear(self) -> None:
        cursor.execute(f"DELETE FROM {self.table_name}")
        connection.commit()
