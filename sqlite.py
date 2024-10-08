import sqlite3

class SQLiteStorage:
    """
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def close(self):
        self.conn.close()

    def execute(self, query, values=None):
        if values:
            self.cursor.execute(query, values)
        else:
            self.cursor.execute(query)
        self.conn.commit()

    def fetchall(self, table):
        self.cursor.execute(f"SELECT * FROM {table}")
        return self.cursor.fetchall()

    def fetchone(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def insert(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        values = tuple(data.values())
        self.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', values)

    def upsert(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        values = tuple(data.values())
        self.execute(f'INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})', values)

    def update(self, table, data, condition):
        set_clause = ', '.join([f'{column} = ?' for column in data.keys()])
        values = tuple(data.values())
        self.execute(f'UPDATE {table} SET {set_clause} WHERE {condition}', values)

    def get(self, table, condition):
        return self.fetchone(f'SELECT * FROM {table} WHERE {condition}')
    
    def get_all(self, table, condition):
        return self.fetchall(f'SELECT * FROM {table} WHERE {condition}')
    
    def delete(self, table, condition):
        self.execute(f'DELETE FROM {table} WHERE {condition}')

    def create_table(self, table, columns):
        self.execute(f'CREATE TABLE IF NOT EXISTS {table} ({columns})')