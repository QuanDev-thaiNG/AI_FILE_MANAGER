import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from actions.mover import FileMover
from actions.tagger import FileTagger
from core.db import Database

class TestFileMover(unittest.TestCase):
    """Kiểm thử cho module FileMover"""
    
    def setUp(self):
        # Tạo database tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init_db()
        
        # Tạo đối tượng FileMover
        self.mover = FileMover(self.db)
        
        # Tạo thư mục nguồn và đích
        self.source_dir = os.path.join(self.temp_dir, "source")
        self.target_dir = os.path.join(self.temp_dir, "target")
        os.makedirs(self.source_dir)
        os.makedirs(self.target_dir)
        
        # Tạo file mẫu
        self.test_file_path = os.path.join(self.source_dir, "test.txt")
        with open(self.test_file_path, 'w') as f:
            f.write("This is a test file.")
    
    def tearDown(self):
        # Xóa database và thư mục tạm thời sau khi kiểm thử
        if hasattr(self, 'db') and self.db:
            self.db.conn.close()
        shutil.rmtree(self.temp_dir)
    
    def test_move_file(self):
        """Kiểm tra di chuyển file"""
        # Đường dẫn đích
        target_path = os.path.join(self.target_dir, "test.txt")
        
        # Di chuyển file
        with patch.object(self.mover, 'log_action') as mock_log_action:
            result = self.mover.move_file(self.test_file_path, target_path)
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.test_file_path))
        self.assertTrue(os.path.exists(target_path))
        
        # Kiểm tra xem hàm log_action đã được gọi không
        mock_log_action.assert_called_once()
    
    def test_copy_file(self):
        """Kiểm tra sao chép file"""
        # Đường dẫn đích
        target_path = os.path.join(self.target_dir, "test.txt")
        
        # Sao chép file
        with patch.object(self.mover, 'log_action') as mock_log_action:
            result = self.mover.copy_file(self.test_file_path, target_path)
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_file_path))
        self.assertTrue(os.path.exists(target_path))
        
        # Kiểm tra xem hàm log_action đã được gọi không
        mock_log_action.assert_called_once()
    
    def test_rename_file(self):
        """Kiểm tra đổi tên file"""
        # Đường dẫn đích
        target_path = os.path.join(self.source_dir, "renamed.txt")
        
        # Đổi tên file
        with patch.object(self.mover, 'log_action') as mock_log_action:
            result = self.mover.rename_file(self.test_file_path, target_path)
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.test_file_path))
        self.assertTrue(os.path.exists(target_path))
        
        # Kiểm tra xem hàm log_action đã được gọi không
        mock_log_action.assert_called_once()
    
    def test_execute_action_plan(self):
        """Kiểm tra thực thi kế hoạch hành động"""
        # Tạo kế hoạch hành động
        action_plan = {
            'file_id': 1,
            'source_path': self.test_file_path,
            'action': 'move',
            'target_path': os.path.join(self.target_dir, "test.txt"),
            'tags': ['test']
        }
        
        # Thực thi kế hoạch hành động
        with patch.object(self.mover, 'move_file', return_value=True) as mock_move_file:
            with patch.object(self.mover, 'log_action') as mock_log_action:
                with patch('actions.tagger.FileTagger.add_tags') as mock_add_tags:
                    result = self.mover.execute_action_plan(action_plan)
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        
        # Kiểm tra xem các hàm đã được gọi không
        mock_move_file.assert_called_once()
        mock_log_action.assert_called_once()
        mock_add_tags.assert_called_once()

class TestFileTagger(unittest.TestCase):
    """Kiểm thử cho module FileTagger"""
    
    def setUp(self):
        # Tạo database tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init_db()
        
        # Tạo đối tượng FileTagger
        self.tagger = FileTagger(self.db)
        
        # Thêm file mẫu vào database
        self.file_info = {
            'abs_path': '/path/to/test.txt',
            'filename': 'test.txt',
            'directory': '/path/to',
            'size': 1024,
            'mime_type': 'text/plain',
            'created_at': '2023-01-01 00:00:00',
            'modified_at': '2023-01-01 00:00:00',
            'hash': 'abcdef1234567890'
        }
        self.file_id = self.db.add_file(self.file_info)
    
    def tearDown(self):
        # Xóa database và thư mục tạm thời sau khi kiểm thử
        if hasattr(self, 'db') and self.db:
            self.db.conn.close()
        shutil.rmtree(self.temp_dir)
    
    @patch('sqlite3.connect')
    def test_add_tag(self, mock_connect):
        """Kiểm tra thêm thẻ"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm thêm thẻ
        result = self.tagger.add_tag(self.file_id, "test_tag")
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('sqlite3.connect')
    def test_remove_tag(self, mock_connect):
        """Kiểm tra xóa thẻ"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm xóa thẻ
        result = self.tagger.remove_tag(self.file_id, "test_tag")
        
        # Kiểm tra kết quả
        self.assertTrue(result)
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('sqlite3.connect')
    def test_get_file_tags(self, mock_connect):
        """Kiểm tra lấy danh sách thẻ của file"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'tag_name': 'tag1'},
            {'tag_name': 'tag2'}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm lấy danh sách thẻ
        tags = self.tagger.get_file_tags(self.file_id)
        
        # Kiểm tra kết quả
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'tag1')
        self.assertEqual(tags[1], 'tag2')
        
        # Kiểm tra xem hàm execute đã được gọi với tham số đúng không
        mock_cursor.execute.assert_called()
    
    @patch('sqlite3.connect')
    def test_list_all_tags(self, mock_connect):
        """Kiểm tra lấy danh sách tất cả các thẻ"""
        # Tạo mock cho kết nối database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'tag_name': 'tag1', 'count': 5},
            {'tag_name': 'tag2', 'count': 3}
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Gọi hàm lấy danh sách tất cả các thẻ
        tags = self.tagger.list_all_tags()
        
        # Kiểm tra kết quả
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0]['tag_name'], 'tag1')
        self.assertEqual(tags[0]['count'], 5)
        self.assertEqual(tags[1]['tag_name'], 'tag2')
        self.assertEqual(tags[1]['count'], 3)
        
        # Kiểm tra xem hàm execute đã được gọi không
        mock_cursor.execute.assert_called()

if __name__ == '__main__':
    unittest.main()