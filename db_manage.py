import sqlite3

import config
from services import Services

# with sqlite3.connect(config.DATABASE) as connection:
#     cursor = connection.cursor()

with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


class TableNameError(Exception):
    pass


class Item:
    ACTUAL = 'actual'
    IRRELEVANT = 'irrelevant'
    PRIORITY_1 = '\U00002780'
    PRIORITY_2 = '\U00002781'
    __items = list()

    def __init__(self, name):
        self.__name = name
        self.__status = self.ACTUAL
        self.__priority = self.PRIORITY_1
        self.__class__.__items.append(self)

    @property
    def name(self):
        return self.__name

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, new_status):
        self.__status = new_status

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self, new_priority):
        self.__priority = new_priority


class Table:
    """
    Базовый клас для списков, нпр списка покупок или списка дел, определяемых как дочерние классы
    Base class for lists, s.a. shopping lists or task lists defined as subclusses
    """
    __list_of_actual = list()
    __list_of_irrelevant = list()
    __list_of_all = list()
    __updated_time = str()

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

    def get_items(self, status: str) -> list:
        __list_of_items = list(
            map(lambda x: x[0],
                cursor.execute(f'SELECT item FROM {self.__table_name} WHERE status = {status}').fetchall())
        )
        return __list_of_items

    def get_all_items(self) -> list:
        __list_of_all = list(map(lambda x: x[0], cursor.execute(f'SELECT item FROM {self.__table_name}').fetchall()))
        return __list_of_all

    def change_status(self, item: Item) -> None:
        """
        Меняет актуальность и приоритет записи
        """
        cursor.execute(
            f'UPDATE {self.table_name} SET status = "{item.status}", priority = "{item.priority}" WHERE item = "{item}"'
        )
        self.set_timestamp()
        connection.commit()

    def add_new_item(self, item: Item) -> None:
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        cursor.execute(f'INSERT INTO {self.table_name} VALUES ("{item.name}", "{item.status}", "{item.priority}")')
        self.set_timestamp()
        connection.commit()

    def delete_item(self, item: str) -> None:
        """
        Удаляет товар из БД
        """
        cursor.execute(f'DELETE FROM {self.__table_name} WHERE item = "{item}"')
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
        cursor.execute(f'INSERT INTO {self.__table_name} VALUES ({user_id}, {Services.get_datetime()}, {repr(msg)})')
        connection.commit()

    @property
    def blocked(self) -> list:
        blocked = cursor.execute(f'SELECT * FROM {self.__table_name}').fetchall()
        return blocked

    def clear(self) -> None:
        cursor.execute(f'DELETE FROM {self.__table_name}')
        connection.commit()
