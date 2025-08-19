import sqlite3
import os
from datetime import datetime
from pathlib import Path

class Database:
    """Lớp quản lý kết nối và thao tác với cơ sở dữ liệu SQLite"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Khởi tạo kết nối và tạo các bảng nếu chưa tồn tại"""
        # Tạo thư mục chứa database nếu chưa tồn tại
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Kết nối đến database
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Trả về kết quả dạng dictionary
        
        # Tạo các bảng
        self._create_tables()
    
    def _create_tables(self):
        """Tạo các bảng trong database"""
        cursor = self.conn.cursor()
        
        # Bảng files
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abs_path TEXT UNIQUE,
            root_id TEXT,
            filename TEXT,
            ext TEXT,
            mimetype TEXT,
            size INTEGER,
            hash_sha256 TEXT,
            created_ts TIMESTAMP,
            modified_ts TIMESTAMP,
            ingested_ts TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
        ''')
        
        # Bảng metadata_media
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            width INTEGER,
            height INTEGER,
            camera_model TEXT,
            datetime TIMESTAMP,
            gps_lat REAL,
            gps_lon REAL,
            duration REAL,
            codec TEXT,
            fps REAL,
            resolution TEXT,
            bitrate INTEGER,
            samplerate INTEGER,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        ''')
        
        # Bảng metadata_doc
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata_doc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            pages INTEGER,
            language TEXT,
            title TEXT,
            author TEXT,
            keywords TEXT,
            has_ocr BOOLEAN,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        ''')
        
        # Bảng content_index
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            plain_text TEXT,
            tokens TEXT,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        ''')
        
        # Bảng embeddings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            model TEXT,
            vector_ref TEXT,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        ''')
        
        # Bảng tags
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT
        )
        ''')
        
        # Bảng file_tags (n-n)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (file_id) REFERENCES files (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id),
            UNIQUE(file_id, tag_id)
        )
        ''')
        
        # Bảng actions_log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            action_type TEXT,
            source_path TEXT,
            target_path TEXT,
            timestamp TIMESTAMP,
            status TEXT,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_file(self, file_data):
        """Thêm hoặc cập nhật thông tin file"""
        cursor = self.conn.cursor()
        
        # Kiểm tra xem file đã tồn tại chưa
        cursor.execute("SELECT id FROM files WHERE abs_path = ?", (file_data['abs_path'],))
        existing = cursor.fetchone()
        
        if existing:
            # Cập nhật thông tin nếu file đã tồn tại
            file_id = existing['id']
            cursor.execute('''
            UPDATE files SET 
                mimetype = ?, size = ?, hash_sha256 = ?, 
                modified_ts = ?, ingested_ts = ?
            WHERE id = ?
            ''', (file_data['mimetype'], file_data['size'], file_data['hash_sha256'], 
                  file_data['modified_ts'], file_data['ingested_ts'], file_id))
        else:
            # Thêm file mới vào DB
            cursor.execute('''
            INSERT INTO files (
                abs_path, root_id, filename, ext, mimetype, 
                size, hash_sha256, created_ts, modified_ts, ingested_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_data['abs_path'], file_data['root_id'], file_data['filename'], 
                  file_data['ext'], file_data['mimetype'], file_data['size'], 
                  file_data['hash_sha256'], file_data['created_ts'], 
                  file_data['modified_ts'], file_data['ingested_ts']))
            file_id = cursor.lastrowid
        
        self.conn.commit()
        return file_id
    
    def add_media_metadata(self, file_id, metadata):
        """Thêm metadata cho file media (ảnh, video, audio)"""
        cursor = self.conn.cursor()
        
        # Kiểm tra xem metadata đã tồn tại chưa
        cursor.execute("SELECT id FROM metadata_media WHERE file_id = ?", (file_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Cập nhật metadata nếu đã tồn tại
            cursor.execute('''
            UPDATE metadata_media SET 
                width = ?, height = ?, camera_model = ?, datetime = ?,
                gps_lat = ?, gps_lon = ?, duration = ?, codec = ?,
                fps = ?, resolution = ?, bitrate = ?, samplerate = ?
            WHERE file_id = ?
            ''', (metadata.get('width'), metadata.get('height'), 
                  metadata.get('camera_model'), metadata.get('datetime'),
                  metadata.get('gps_lat'), metadata.get('gps_lon'),
                  metadata.get('duration'), metadata.get('codec'),
                  metadata.get('fps'), metadata.get('resolution'),
                  metadata.get('bitrate'), metadata.get('samplerate'),
                  file_id))
        else:
            # Thêm metadata mới
            cursor.execute('''
            INSERT INTO metadata_media (
                file_id, width, height, camera_model, datetime,
                gps_lat, gps_lon, duration, codec, fps, resolution,
                bitrate, samplerate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, metadata.get('width'), metadata.get('height'),
                  metadata.get('camera_model'), metadata.get('datetime'),
                  metadata.get('gps_lat'), metadata.get('gps_lon'),
                  metadata.get('duration'), metadata.get('codec'),
                  metadata.get('fps'), metadata.get('resolution'),
                  metadata.get('bitrate'), metadata.get('samplerate')))
        
        self.conn.commit()
    
    def add_doc_metadata(self, file_id, metadata):
        """Thêm metadata cho file tài liệu (PDF, DOCX, ...)"""
        cursor = self.conn.cursor()
        
        # Kiểm tra xem metadata đã tồn tại chưa
        cursor.execute("SELECT id FROM metadata_doc WHERE file_id = ?", (file_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Cập nhật metadata nếu đã tồn tại
            cursor.execute('''
            UPDATE metadata_doc SET 
                pages = ?, language = ?, title = ?, author = ?,
                keywords = ?, has_ocr = ?
            WHERE file_id = ?
            ''', (metadata.get('pages'), metadata.get('language'),
                  metadata.get('title'), metadata.get('author'),
                  metadata.get('keywords'), metadata.get('has_ocr'),
                  file_id))
        else:
            # Thêm metadata mới
            cursor.execute('''
            INSERT INTO metadata_doc (
                file_id, pages, language, title, author, keywords, has_ocr
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, metadata.get('pages'), metadata.get('language'),
                  metadata.get('title'), metadata.get('author'),
                  metadata.get('keywords'), metadata.get('has_ocr')))
        
        self.conn.commit()
    
    def add_content_index(self, file_id, plain_text, tokens=None):
        """Thêm nội dung đã chuẩn hoá và tokens cho file"""
        cursor = self.conn.cursor()
        
        # Kiểm tra xem content đã tồn tại chưa
        cursor.execute("SELECT id FROM content_index WHERE file_id = ?", (file_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Cập nhật content nếu đã tồn tại
            cursor.execute('''
            UPDATE content_index SET 
                plain_text = ?, tokens = ?
            WHERE file_id = ?
            ''', (plain_text, tokens, file_id))
        else:
            # Thêm content mới
            cursor.execute('''
            INSERT INTO content_index (
                file_id, plain_text, tokens
            ) VALUES (?, ?, ?)
            ''', (file_id, plain_text, tokens))
        
        self.conn.commit()
    
    def log_action(self, file_id, action_type, source_path, target_path=None, status='completed'):
        """Ghi lại hành động vào nhật ký"""
        cursor = self.conn.cursor()
        timestamp = datetime.now()
        
        cursor.execute('''
        INSERT INTO actions_log (
            file_id, action_type, source_path, target_path, timestamp, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_id, action_type, source_path, target_path, timestamp, status))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_action_status(self, action_id, status):
        """Cập nhật trạng thái của hành động"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE actions_log SET status = ? WHERE id = ?", (status, action_id))
        self.conn.commit()
    
    def get_file_by_path(self, abs_path):
        """Lấy thông tin file theo đường dẫn tuyệt đối"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE abs_path = ?", (abs_path,))
        return cursor.fetchone()
    
    def get_file_by_hash(self, hash_sha256):
        """Lấy thông tin file theo hash SHA-256"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE hash_sha256 = ?", (hash_sha256,))
        return cursor.fetchall()
    
    def search_files(self, query_params):
        """Tìm kiếm file theo các tham số"""
        cursor = self.conn.cursor()
        
        # Xây dựng câu truy vấn SQL
        sql = "SELECT f.* FROM files f"
        params = []
        where_clauses = []
        
        # Thêm join nếu cần
        if query_params.get('tag'):
            sql += " JOIN file_tags ft ON f.id = ft.file_id JOIN tags t ON ft.tag_id = t.id"
            where_clauses.append("t.name = ?")
            params.append(query_params['tag'])
        
        # Thêm các điều kiện tìm kiếm
        if query_params.get('name'):
            where_clauses.append("f.filename LIKE ?")
            params.append(f"%{query_params['name']}%")
        
        if query_params.get('ext'):
            where_clauses.append("f.ext = ?")
            params.append(query_params['ext'])
        
        if query_params.get('mimetype'):
            where_clauses.append("f.mimetype LIKE ?")
            params.append(f"%{query_params['mimetype']}%")
        
        if query_params.get('since'):
            where_clauses.append("f.modified_ts >= ?")
            params.append(query_params['since'])
        
        if query_params.get('status'):
            where_clauses.append("f.status = ?")
            params.append(query_params['status'])
        
        # Thêm điều kiện WHERE nếu có
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        # Thực hiện truy vấn
        cursor.execute(sql, params)
        return cursor.fetchall()
    
    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()
            self.conn = None