# import pytest
from db_manage import Shopping
from sqlite3 import *

def test_create_table():
    table_name = 'test_table'
    Shopping.create_table(table_name)


