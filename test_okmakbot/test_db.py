# import pytest
from db_manage import Shopping, db_request


def test_create_table():
    table_name = 'test_table'
    Shopping.create_table(table_name)
    # print(table.fetchall())

