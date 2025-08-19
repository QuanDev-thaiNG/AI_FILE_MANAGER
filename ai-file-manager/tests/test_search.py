import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.indexer import ContentIndexer
from search.searcher import FileSearcher
from core.db import Database

class TestContentIndexer(unittest.TestCase):
    """Kiểm thử cho module ContentIndexer"""
    
    def setUp(self):
        # Tạo database tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init_db()
        
        # Tạo đối tượng ContentIndexer với mock cho sentence_transformers
        with patch('sentence_transformers.SentenceTransformer'):
            self.indexer = ContentIndexer(self.db)
    
    def tearDown(self):
        # Xóa database và thư mục tạm thời sau khi kiểm thử
        if hasattr(self, 'db') and self.db:
            self.db.conn.close()
        shutil.rmtree(self.temp_dir)
    
    def test_chunk_text(self):
        """Kiểm tra chia nhỏ văn bản thành các đoạn"""
        # Tạo văn bản mẫu
        text = "Đây là đoạn văn bản mẫu. Nó có nhiều câu. Mỗi câu có thể được chia thành các đoạn nhỏ. " * 10
        
        # Chia nhỏ văn bản với kích thước đoạn là 100 và độ chồng lấp là 20
        chunks = self.indexer.chunk_text(text, chunk_size=100, overlap=20)
        
        # Kiểm tra số lượng đoạn
        self.assertGreater(len(chunks), 1)
        
        # Kiểm tra kích thước đoạn
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)
        
        # Kiểm tra độ chồng lấp giữa các đoạn
        for i in range(len(chunks) - 1):
            overlap_text = chunks[i][-20:]
            self.assertTrue(chunks[i+1].startswith(overlap_text))
    
    @patch('sqlite3.connect')
    def test_index_text_content(self, mock_connect):
        """Kiểm tra lập chỉ mục nội dung văn bản"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Tạo thông tin file mẫu
        file_info = {
            'id': 1,
            'abs_path': '/path/to/test.txt',
            'filename': 'test.txt',
            'mime_type': 'text/plain'
        }
        
        # Tạo nội dung văn bản mẫu
        text_content = "Đây là nội dung văn bản mẫu để kiểm tra lập chỉ mục."
        
        # Gọi hàm lập chỉ mục nội dung văn bản
        with patch.object(self.indexer, 'chunk_text', return_value=[text_content]):
            self.indexer.index_text_content(file_info, text_content)
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
        
        # Kiểm tra xem hàm commit đã được gọi không
        mock_conn.commit.assert_called()
    
    @patch('sqlite3.connect')
    def test_search_by_keyword(self, mock_connect):
        """Kiểm tra tìm kiếm theo từ khóa"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'file_id': 1, 'filename': 'test1.txt', 'abs_path': '/path/to/test1.txt', 'content': 'Đây là nội dung văn bản mẫu.'},
            {'file_id': 2, 'filename': 'test2.txt', 'abs_path': '/path/to/test2.txt', 'content': 'Đây là một văn bản mẫu khác.'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm theo từ khóa
        results = self.indexer.search_by_keyword("văn bản mẫu")
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['filename'], 'test1.txt')
        self.assertEqual(results[1]['filename'], 'test2.txt')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()

class TestFileSearcher(unittest.TestCase):
    """Kiểm thử cho module FileSearcher"""
    
    def setUp(self):
        # Tạo database tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init_db()
        
        # Tạo đối tượng FileSearcher
        self.searcher = FileSearcher(self.db)
    
    def tearDown(self):
        # Xóa database và thư mục tạm thời sau khi kiểm thử
        if hasattr(self, 'db') and self.db:
            self.db.conn.close()
        shutil.rmtree(self.temp_dir)
    
    @patch('sqlite3.connect')
    def test_search_by_filename(self, mock_connect):
        """Kiểm tra tìm kiếm theo tên file"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'filename': 'test.txt', 'abs_path': '/path/to/test.txt'},
            {'id': 2, 'filename': 'test.pdf', 'abs_path': '/path/to/test.pdf'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm theo tên file
        results = self.searcher.search_by_filename("test")
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['filename'], 'test.txt')
        self.assertEqual(results[1]['filename'], 'test.pdf')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
    
    @patch('sqlite3.connect')
    def test_search_by_mimetype(self, mock_connect):
        """Kiểm tra tìm kiếm theo MIME type"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'filename': 'test1.jpg', 'abs_path': '/path/to/test1.jpg', 'mime_type': 'image/jpeg'},
            {'id': 2, 'filename': 'test2.jpg', 'abs_path': '/path/to/test2.jpg', 'mime_type': 'image/jpeg'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm theo MIME type
        results = self.searcher.search_by_mimetype("image/jpeg")
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['filename'], 'test1.jpg')
        self.assertEqual(results[1]['filename'], 'test2.jpg')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
    
    @patch('sqlite3.connect')
    def test_search_by_tags(self, mock_connect):
        """Kiểm tra tìm kiếm theo thẻ"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'filename': 'test1.jpg', 'abs_path': '/path/to/test1.jpg', 'tag_name': 'ảnh'},
            {'id': 2, 'filename': 'test2.jpg', 'abs_path': '/path/to/test2.jpg', 'tag_name': 'ảnh'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm theo thẻ
        results = self.searcher.search_by_tags(["ảnh"])
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['filename'], 'test1.jpg')
        self.assertEqual(results[1]['filename'], 'test2.jpg')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
    
    @patch('sqlite3.connect')
    def test_find_duplicates(self, mock_connect):
        """Kiểm tra tìm kiếm file trùng lặp"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'hash': 'abc123', 'count': 2, 'files': 'test1.jpg,test2.jpg'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm file trùng lặp
        results = self.searcher.find_duplicates()
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['hash'], 'abc123')
        self.assertEqual(results[0]['count'], 2)
        self.assertEqual(results[0]['files'], 'test1.jpg,test2.jpg')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
    
    @patch('sqlite3.connect')
    def test_search(self, mock_connect):
        """Kiểm tra tìm kiếm tổng hợp"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'filename': 'test.jpg', 'abs_path': '/path/to/test.jpg', 'mime_type': 'image/jpeg'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm tìm kiếm tổng hợp
        results = self.searcher.search(
            filename="test",
            extension=".jpg",
            mime_type="image/jpeg",
            tags=["ảnh"],
            min_size=1000,
            max_size=10000,
            created_after="2023-01-01",
            created_before="2023-12-31"
        )
        
        # Kiểm tra kết quả
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['filename'], 'test.jpg')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()

if __name__ == '__main__':
    unittest.main()