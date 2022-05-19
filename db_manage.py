import sqlite3
from sqlite3 import Cursor

import config

from services import Services


with sqlite3.connect(config.DATABASE) as connection:
    cursor = connection.cursor()


def db_request(command: str) -> Cursor:
    cursor.execute(command)
    connection.commit()
    # connection.close()


class Base:
    __table = ''
    __actual_list = []
    __irrelevant_list = []
    __all_items = []

    @classmethod
    def create_table(cls, table_name) -> None:
        cls.__table = table_name
        # cls.table_name = table
        # cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        db_request(f'CREATE TABLE IF NOT EXISTS {table_name} (item VARCHAR(32), status VARCHAR(32))')


    @classmethod
    @property
    def all_items(cls) -> list:
        list_of_all = list(map(lambda x: x[0], db_request(f'SELECT item FROM {cls.__table}').fetchall()))
        return list_of_all

    @classmethod
    @property
    def irrelevant_items(cls) -> list:
        list_of_irrelevant = list(
            map(lambda x: x[0], db_request(f'SELECT item FROM {cls.__table} WHERE status = "irrelevant"').fetchall())
        )
        return list_of_irrelevant

    @classmethod
    @property
    def actual_items(cls) -> list:
        list_of_actual = list(
            map(lambda x: x[0], db_request(f'SELECT item FROM {cls.__table} WHERE status = "actual"').fetchall())
        )
        return list_of_actual

    @classmethod
    def set_actual(cls, item):
        """
        Меняет состояние сущности из неактуального на актульное
        """
        db_request(f'UPDATE {cls.__table} SET status = "actual" WHERE item = "{item}"')
        cls.set_timestamp()

    @classmethod
    def set_irrelevant(cls, item: str) -> None:
        """
        Меняет состояние сущности из актуалнього на неактульное
        """
        db_request(f'UPDATE {cls.__table} SET status = "irrelevant" WHERE item = "{item}"')
        cls.set_timestamp()

    @classmethod
    def add_new_item(cls, new_item):
        """
        Добавляет новую запись в БД и задает его состояние как актуальное
        """
        if new_item not in cls.all_items:
            db_request(f'INSERT INTO {cls.__table} VALUES ("{new_item}", "actual")')
        cls.set_timestamp()

    @classmethod
    def delete_item(cls, item: str) -> None:
        """
        Удалаяет товар из БД
        """
        db_request(f'DELETE FROM {cls.__table} WHERE item = "{item}"')

    @classmethod
    def set_timestamp(cls):
        cls.updated_time = Services.get_datetime()


class Shopping(Base):
    TABLE_NAME = 'product'

    def __init__(self):
        super().create_table(self.TABLE_NAME)


class ToDo(Base):
    TABLE_NAME = 'todo'

    def __init__(self):
        super().create_table(self.TABLE_NAME)


# class Blocked():
#     TABLE_NAME = 'blocked'
#
#     def __init__(self):
#         db_request(f'CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (user_id INTEGER, datetime TEXT, msg TEXT)')
#
#     def add(self, user_id, msg):
#         db_request(f'INSERT INTO {cls.TABLE_NAME} VALUES ({user_id}, {Services.get_datetime()}, {repr(msg)})')
#
#     def get_blocked(self):
#         blocked = db_request(f'SELECT * FROM {cls.TABLE_NAME}").fetchall()')
#         return blocked
#
#     @staticmethod
#     def clear_list(self):
#         db_request(f'DELETE FROM {cls.TABLE_NAME}')
