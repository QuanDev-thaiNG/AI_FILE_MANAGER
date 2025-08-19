from pathlib import Path
import hashlib
import os
import time
try:
    import magic  # pip install python-magic
except ImportError:
    from core.magic_wrapper import detect_mime_type
import sqlite3
from datetime import datetime

class FileIngestor:
    """Quét thư mục, lấy hash, phát hiện trùng lặp, thu thập metadata cơ bản"""
    
    def __init__(self, db_or_path):
        self.db = None
        self.conn = None
        
        if isinstance(db_or_path, str) or isinstance(db_or_path, Path):
            # Nếu là đường dẫn
            self.db_path = db_or_path
            self.init_db()
        else:
            # Nếu là đối tượng Database
            self.db = db_or_path
            self.conn = self.db.conn
    
    def init_db(self):
        """Khởi tạo kết nối database và tạo bảng nếu chưa tồn tại"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Tạo bảng files nếu chưa tồn tại
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
        
        # Tạo bảng actions_log
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
    
    def iter_files(self, path=None, recursive=True):
        """Duyệt qua tất cả các file trong thư mục"""
        if path is None:
            path = self.root
        path = Path(path)
        
        if recursive:
            for p in path.rglob('*'):
                if p.is_file():
                    yield p
        else:
            for p in path.iterdir():
                if p.is_file():
                    yield p
    
    def hash_sha256(self, p: Path):
        """Tính toán hash SHA-256 của file"""
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1<<20), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def detect_mime(self, p: Path):
        """Phát hiện kiểu MIME của file"""
        try:
            # Thử sử dụng thư viện magic nếu đã import thành công
            if 'magic' in globals():
                return magic.from_file(str(p), mime=True)
            else:
                # Sử dụng magic_wrapper nếu không có thư viện magic
                return detect_mime_type(str(p))
        except Exception as e:
            print(f"Lỗi khi phát hiện MIME cho {p}: {e}")
            return "application/octet-stream"
    
    def ingest_file(self, file_path, root_path=None, dry_run=False):
        """Đăng ký một file vào database"""
        if not self.conn and not dry_run:
            raise ValueError("Database chưa được khởi tạo")
        
        try:
            p = Path(file_path)
            if not p.exists() or not p.is_file():
                return False
            
            # Thu thập thông tin cơ bản
            abs_path = str(p.absolute())
            root_id = str(root_path) if root_path else os.path.dirname(abs_path)
            filename = p.name
            ext = p.suffix.lower().lstrip('.')
            
            mimetype = self.detect_mime(p)
            size = p.stat().st_size
            
            if dry_run:
                print(f"[Dry run] Sẽ đăng ký file: {abs_path}")
                return True
                
            # Kiểm tra xem file đã tồn tại trong database chưa
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM files WHERE abs_path = ?", (abs_path,))
            existing = cursor.fetchone()
            
            if existing:
                # Cập nhật thông tin nếu file đã tồn tại
                cursor.execute("""
                UPDATE files SET 
                    mimetype = ?, size = ?, modified_ts = ?
                WHERE abs_path = ?
                """, (mimetype, size, datetime.fromtimestamp(p.stat().st_mtime), abs_path))
            else:
                # Thêm mới nếu file chưa tồn tại
                cursor.execute("""
                INSERT INTO files (
                    abs_path, root_id, filename, ext, mimetype, size, 
                    hash_sha256, created_ts, modified_ts, ingested_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    abs_path, root_id, filename, ext, mimetype, size,
                    self.hash_sha256(p), 
                    datetime.fromtimestamp(p.stat().st_ctime),
                    datetime.fromtimestamp(p.stat().st_mtime),
                    datetime.now()
                ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Lỗi khi đăng ký file {file_path}: {str(e)}")
            return False
            
    def ingest_directory(self, directory_path, recursive=True, dry_run=False):
        """Đăng ký tất cả các file trong một thư mục vào database"""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            print(f"Thư mục không tồn tại: {directory_path}")
            return 0
            
        count = 0
        for file_path in self.iter_files(directory, recursive):
            try:
                result = self.ingest_file(file_path, root_path=directory_path, dry_run=dry_run)
                if result:
                    count += 1
            except Exception as e:
                print(f"Lỗi khi đăng ký file {file_path}: {str(e)}")
                
        return count
    

    
    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Hàm tiện ích để sắp xếp file đơn giản theo đuôi
def simple_sort(src_dir, dst_dir):
    """Sắp xếp file đơn giản theo đuôi file"""
    src, dst = Path(src_dir), Path(dst_dir)
    dst.mkdir(parents=True, exist_ok=True)
    ing = FileIngestor(src)
    
    for f in ing.iter_files():
        ext = f.suffix.lower().lstrip('.') or 'noext'
        target_dir = dst / ext
        target_dir.mkdir(exist_ok=True)
        
        ts = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y%m%d_%H%M%S')
        new_name = f"{f.stem}_{ts}.{ext}" if ext != 'noext' else f"{f.stem}_{ts}"
        target = target_dir / new_name
        
        print(f"Di chuyển {f} -> {target}")
        shutil.copy2(f, target)  # hoặc move: shutil.move