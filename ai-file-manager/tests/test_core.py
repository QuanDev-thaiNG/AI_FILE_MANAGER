import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database
from core.ingest import FileIngestor
from core.mimetype import MimeTypeDetector
from core.hashing import FileHasher, DuplicateFinder

class TestDatabase(unittest.TestCase):
    """Kiểm thử cho module Database"""
    
    def setUp(self):
        # Tạo database tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init_db()
    
    def tearDown(self):
        # Xóa database và thư mục tạm thời sau khi kiểm thử
        if hasattr(self, 'db') and self.db:
            self.db.conn.close()
        shutil.rmtree(self.temp_dir)
    
    def test_init_db(self):
        """Kiểm tra khởi tạo database"""
        # Kiểm tra xem file database đã được tạo chưa
        self.assertTrue(os.path.exists(self.db_path))
        
        # Kiểm tra xem các bảng đã được tạo chưa
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        expected_tables = [
            'files', 'metadata_media', 'metadata_doc', 'content_index',
            'embeddings', 'tags', 'file_tags', 'actions_log'
        ]
        
        for table in expected_tables:
            self.assertIn(table, tables)
    
    def test_add_file(self):
        """Kiểm tra thêm thông tin file"""
        # Thêm một file mẫu
        file_info = {
            'abs_path': '/path/to/test.txt',
            'filename': 'test.txt',
            'directory': '/path/to',
            'size': 1024,
            'mime_type': 'text/plain',
            'created_at': '2023-01-01 00:00:00',
            'modified_at': '2023-01-01 00:00:00',
            'hash': 'abcdef1234567890'
        }
        
        file_id = self.db.add_file(file_info)
        self.assertIsNotNone(file_id)
        
        # Kiểm tra xem file đã được thêm chưa
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'test.txt')
        self.assertEqual(result['mime_type'], 'text/plain')

class TestMimeTypeDetector(unittest.TestCase):
    """Kiểm thử cho module MimeTypeDetector"""
    
    def setUp(self):
        self.detector = MimeTypeDetector()
    
    def test_get_mimetype_from_extension(self):
        """Kiểm tra lấy MIME type từ phần mở rộng"""
        self.assertEqual(self.detector.get_mimetype_from_extension('.txt'), 'text/plain')
        self.assertEqual(self.detector.get_mimetype_from_extension('.jpg'), 'image/jpeg')
        self.assertEqual(self.detector.get_mimetype_from_extension('.pdf'), 'application/pdf')
        self.assertEqual(self.detector.get_mimetype_from_extension('.mp4'), 'video/mp4')
    
    def test_get_category(self):
        """Kiểm tra lấy danh mục từ MIME type"""
        self.assertEqual(self.detector.get_category('image/jpeg'), 'image')
        self.assertEqual(self.detector.get_category('video/mp4'), 'video')
        self.assertEqual(self.detector.get_category('text/plain'), 'text')
        self.assertEqual(self.detector.get_category('application/pdf'), 'document')
        self.assertEqual(self.detector.get_category('application/octet-stream'), 'other')

class TestFileHasher(unittest.TestCase):
    """Kiểm thử cho module FileHasher"""
    
    def setUp(self):
        self.hasher = FileHasher()
        
        # Tạo file tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test.txt")
        
        with open(self.test_file_path, 'w') as f:
            f.write("This is a test file for hashing.")
    
    def tearDown(self):
        # Xóa thư mục tạm thời sau khi kiểm thử
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_hash(self):
        """Kiểm tra tính toán hash SHA-256"""
        # Tính hash của file kiểm thử
        file_hash = self.hasher.calculate_hash(self.test_file_path)
        
        # Kiểm tra xem hash có đúng định dạng không
        self.assertIsNotNone(file_hash)
        self.assertEqual(len(file_hash), 64)  # SHA-256 hash có độ dài 64 ký tự hex
        
        # Tính lại hash và kiểm tra xem có giống nhau không
        file_hash2 = self.hasher.calculate_hash(self.test_file_path)
        self.assertEqual(file_hash, file_hash2)

if __name__ == '__main__':
    unittest.main()