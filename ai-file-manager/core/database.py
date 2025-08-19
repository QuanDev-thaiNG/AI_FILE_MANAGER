import sqlite3
import os

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Lỗi kết nối đến cơ sở dữ liệu: {e}")
            return False
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def init_database(self):
        try:
            if not self.conn:
                self.connect()
            
            # Tạo bảng files để lưu thông tin tập tin
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                filename TEXT,
                extension TEXT,
                size INTEGER,
                created_date TEXT,
                modified_date TEXT,
                content_hash TEXT,
                mime_type TEXT,
                metadata TEXT,
                extracted_text TEXT,
                embedding_path TEXT
            )
            ''')
            
            # Tạo bảng tags để lưu các tag
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            ''')
            
            # Tạo bảng file_tags để lưu mối quan hệ giữa file và tag
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_tags (
                file_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (file_id, tag_id),
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
            ''')
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Lỗi khởi tạo cơ sở dữ liệu: {e}")
            return False
    
    def execute_query(self, query, params=()):
        try:
            if not self.conn:
                self.connect()
            
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Lỗi thực thi truy vấn: {e}")
            return False
    
    def fetch_query(self, query, params=()):
        try:
            if not self.conn:
                self.connect()
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Lỗi truy vấn dữ liệu: {e}")
            return []