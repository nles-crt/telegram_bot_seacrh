class TelegramURLDatabase:
    def __init__(self, db_name='telegram_URL.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
    def search_users_by_name(self, name, page, page_size=10):
        offset = (page - 1) * page_size
        query = 'SELECT * FROM telegram WHERE name LIKE ? LIMIT ?, ?'
        self.cursor.execute(query, ('%' + name + '%', offset, page_size))
        results = self.cursor.fetchall()
        has_more = len(results) == page_size
        return results, has_more
    
    def insert_record(self, name, telegram_url, type, time, number):
        """
        向数据库中插入一条记录.
        
        Args:
            name (str): 名称.
            telegram_url (str): Telegram URL.
            type (str): 类型.
            time (str): 时间.
            number (str): 数字.
        """
        # 使用参数化查询来插入数据
        query = "INSERT INTO telegram (name, telegram_url, type, time, number) VALUES (?, ?, ?, ?, ?)"
        values = (name, telegram_url, type, time, number)
        self.cursor.execute(query, values)
        self.conn.commit()  # 修复此行,将self.connection改为self.conn
        return 
    def search_record_by_telegram_url(self, telegram_url):
        query = "SELECT * FROM telegram WHERE telegram_url = ?"
        self.cursor.execute(query, (telegram_url,))
        results = self.cursor.fetchone()
        return results
    def get_data_by_page_and_name(self, page_id, name):
        items_per_page = 10
        offset = (page_id - 1) * items_per_page
        query = 'SELECT * FROM telegram WHERE name LIKE ? LIMIT ?, ?'
        self.cursor.execute(query, ('%' + name + '%', offset, items_per_page))
        results = self.cursor.fetchall()
        return results

    def close(self):
        self.conn.close()


tele_url_db = TelegramURLDatabase()