from main import *
from db_manage import *


def test_set_blocked_id():
    id = 123456789
    time = str(get_datetime())
    text = 'testing'
    connection = sqlite3.connect(config.db_path)
    with connection:
        cursor = connection.cursor()
    cursor.execute(f"INSERT INTO blocked_users VALUES ({id}, {time}, {text})")
    connection.commit()
    blocked = cursor.execute(f'SELECT * FROM blocked_users WHERE userID = {id}').fetchone()
    print(blocked)
    assert filtering_users(id) == [id, time, text], 'E'
