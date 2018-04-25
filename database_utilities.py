import sqlite3


class DataBase:
    def __init__(self, name='users.db'):
        self.__file = name
        try:
            conn = sqlite3.connect(self.__file)
            cursor = conn.cursor()
            try:
                cursor.execute('CREATE TABLE users (id INT UNIQUE, token CHAR(200), got INT, life INT)')
                conn.commit()
            except Exception as e:
                print(e)
            print(sqlite3.version, 'version database initialized')
            conn.close()
        except Exception as e:
            print('Something gone wrong')
            print(e)
            quit()

    def __contains__(self, item):
        conn = sqlite3.connect(self.__file)
        curs = conn.cursor()
        curs.execute('SELECT id, token, got, life FROM users WHERE id=' + str(item))
        result = curs.fetchall()
        conn.close()
        return bool(result)

    def remove(self, user_id):
        conn = sqlite3.connect(self.__file)
        curs = conn.cursor()
        curs.execute('DELETE FROM users WHERE id=' + str(user_id))
        conn.commit()
        conn.close()

    def add(self, user_info):
        conn = sqlite3.connect(self.__file)
        curs = conn.cursor()
        req = 'INSERT INTO users VALUES ({id},"{token}",{got},{life})'.format(
            id=user_info[0],
            token=user_info[1],
            got=user_info[2],
            life=user_info[3]
        )
        curs.execute(req)
        conn.commit()
        conn.close()

    def get_info(self, user_id):
        conn = sqlite3.connect(self.__file)
        curs = conn.cursor()
        curs.execute('SELECT id, token, got, life FROM users WHERE id=' + str(user_id))
        result = curs.fetchall()
        conn.close()
        return list(result[0])
