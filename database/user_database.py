import sqlite3
class UserDatabase:
    def __init__(self, db_name='user_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_blacklisted INTEGER
            )
        ''')
        self.conn.commit()
    def get_user_info(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def get_user_info_all(self, limit=10):
        query = 'SELECT * FROM users'
        if limit is not None:
            query += ' LIMIT ?'
            self.cursor.execute(query, (limit,))
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()
    
    
    def add_user(self, user_id, username):
        self.cursor.execute('INSERT INTO users (user_id, username, is_blacklisted) VALUES (?, ?, 0)', (user_id, username))
        self.conn.commit()
    
    def user_exists(self, user_id):
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] > 0

    def is_blacklisted(self, user_id):
        self.cursor.execute('SELECT is_blacklisted FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

    def blacklist_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_blacklisted = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unblacklist_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_blacklisted = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


user_db = UserDatabase()
