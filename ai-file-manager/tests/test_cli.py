import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.commands import CommandHandler

class TestCommandHandler(unittest.TestCase):
    """Kiểm thử cho module CommandHandler"""
    
    def setUp(self):
        # Tạo thư mục tạm thời cho kiểm thử
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # Tạo đối tượng CommandHandler
        self.handler = CommandHandler()
    
    def tearDown(self):
        # Xóa thư mục tạm thời sau khi kiểm thử
        shutil.rmtree(self.temp_dir)
    
    @patch('core.db.Database')
    def test_init_command(self, mock_database):
        """Kiểm tra lệnh init"""
        # Tạo mock cho Database
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        # Tạo tham số cho lệnh init
        args = MagicMock()
        args.db_path = self.db_path
        
        # Gọi lệnh init
        self.handler.handle_init(args)
        
        # Kiểm tra xem Database đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_db.init_db.assert_called_once()
    
    @patch('core.ingest.FileIngestor')
    @patch('core.db.Database')
    def test_ingest_command(self, mock_database, mock_ingestor):
        """Kiểm tra lệnh ingest"""
        # Tạo mock cho Database và FileIngestor
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        mock_fi = MagicMock()
        mock_ingestor.return_value = mock_fi
        
        # Tạo tham số cho lệnh ingest
        args = MagicMock()
        args.db_path = self.db_path
        args.directory = self.temp_dir
        args.recursive = True
        args.dry_run = False
        
        # Gọi lệnh ingest
        self.handler.handle_ingest(args)
        
        # Kiểm tra xem Database và FileIngestor đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_ingestor.assert_called_once_with(mock_db)
        
        # Kiểm tra xem phương thức ingest_directory đã được gọi chưa
        mock_fi.ingest_directory.assert_called_once_with(
            self.temp_dir, recursive=True, dry_run=False
        )
    
    @patch('rules.engine.RulesEngine')
    @patch('actions.mover.FileMover')
    @patch('core.db.Database')
    def test_organize_command(self, mock_database, mock_mover, mock_rules_engine):
        """Kiểm tra lệnh organize"""
        # Tạo mock cho Database, FileMover và RulesEngine
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        mock_fm = MagicMock()
        mock_mover.return_value = mock_fm
        
        mock_re = MagicMock()
        mock_rules_engine.return_value = mock_re
        
        # Tạo mock cho kết quả truy vấn database
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'abs_path': '/path/to/test.txt', 'filename': 'test.txt'}
        ]
        mock_db.conn.cursor.return_value = mock_cursor
        
        # Tạo mock cho kết quả áp dụng quy tắc
        mock_re.apply_rules.return_value = {
            'action': 'move',
            'target_path': '/path/to/target/test.txt',
            'tags': ['test']
        }
        
        # Tạo tham số cho lệnh organize
        args = MagicMock()
        args.db_path = self.db_path
        args.rules_file = 'rules.yaml'
        args.dry_run = False
        
        # Gọi lệnh organize
        self.handler.handle_organize(args)
        
        # Kiểm tra xem các đối tượng đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_mover.assert_called_once_with(mock_db)
        mock_rules_engine.assert_called_once_with('rules.yaml')
        
        # Kiểm tra xem phương thức execute_action_plan đã được gọi chưa
        mock_fm.execute_action_plan.assert_called()
    
    @patch('search.searcher.FileSearcher')
    @patch('core.db.Database')
    def test_search_command(self, mock_database, mock_searcher):
        """Kiểm tra lệnh search"""
        # Tạo mock cho Database và FileSearcher
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        mock_fs = MagicMock()
        mock_searcher.return_value = mock_fs
        
        # Tạo mock cho kết quả tìm kiếm
        mock_fs.search.return_value = [
            {'id': 1, 'filename': 'test.txt', 'abs_path': '/path/to/test.txt'}
        ]
        
        # Tạo tham số cho lệnh search
        args = MagicMock()
        args.db_path = self.db_path
        args.filename = 'test'
        args.extension = None
        args.mime_type = None
        args.tags = None
        args.min_size = None
        args.max_size = None
        args.created_after = None
        args.created_before = None
        
        # Gọi lệnh search
        self.handler.handle_search(args)
        
        # Kiểm tra xem các đối tượng đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_searcher.assert_called_once_with(mock_db)
        
        # Kiểm tra xem phương thức search đã được gọi chưa
        mock_fs.search.assert_called_once()
    
    @patch('actions.tagger.FileTagger')
    @patch('core.db.Database')
    def test_tag_command(self, mock_database, mock_tagger):
        """Kiểm tra lệnh tag"""
        # Tạo mock cho Database và FileTagger
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        mock_ft = MagicMock()
        mock_tagger.return_value = mock_ft
        
        # Tạo mock cho kết quả truy vấn database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_db.conn.cursor.return_value = mock_cursor
        
        # Tạo tham số cho lệnh tag (add)
        args = MagicMock()
        args.db_path = self.db_path
        args.action = 'add'
        args.file_path = '/path/to/test.txt'
        args.tags = ['test1', 'test2']
        
        # Gọi lệnh tag (add)
        self.handler.handle_tag(args)
        
        # Kiểm tra xem các đối tượng đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_tagger.assert_called_once_with(mock_db)
        
        # Kiểm tra xem phương thức add_tags đã được gọi chưa
        mock_ft.add_tags.assert_called_once_with(1, ['test1', 'test2'])
        
        # Tạo tham số cho lệnh tag (remove)
        args.action = 'remove'
        
        # Gọi lệnh tag (remove)
        self.handler.handle_tag(args)
        
        # Kiểm tra xem phương thức remove_tags đã được gọi chưa
        mock_ft.remove_tags.assert_called_once_with(1, ['test1', 'test2'])
        
        # Tạo tham số cho lệnh tag (list)
        args.action = 'list'
        args.file_path = None
        
        # Tạo mock cho kết quả list_all_tags
        mock_ft.list_all_tags.return_value = [
            {'tag_name': 'test1', 'count': 5},
            {'tag_name': 'test2', 'count': 3}
        ]
        
        # Gọi lệnh tag (list)
        self.handler.handle_tag(args)
        
        # Kiểm tra xem phương thức list_all_tags đã được gọi chưa
        mock_ft.list_all_tags.assert_called_once()
    
    @patch('search.indexer.ContentIndexer')
    @patch('core.db.Database')
    def test_index_command(self, mock_database, mock_indexer):
        """Kiểm tra lệnh index"""
        # Tạo mock cho Database và ContentIndexer
        mock_db = MagicMock()
        mock_database.return_value = mock_db
        
        mock_ci = MagicMock()
        mock_indexer.return_value = mock_ci
        
        # Tạo mock cho kết quả truy vấn database
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'abs_path': '/path/to/test.txt', 'filename': 'test.txt', 'mime_type': 'text/plain'}
        ]
        mock_db.conn.cursor.return_value = mock_cursor
        
        # Tạo tham số cho lệnh index
        args = MagicMock()
        args.db_path = self.db_path
        args.rebuild = True
        args.mime_type = 'text/plain'
        
        # Gọi lệnh index
        with patch('builtins.open', MagicMock()):
            with patch('extractors.pdfs.PDFExtractor.extract_text', return_value="Test content"):
                self.handler.handle_index(args)
        
        # Kiểm tra xem các đối tượng đã được khởi tạo chưa
        mock_database.assert_called_once_with(self.db_path)
        mock_indexer.assert_called_once_with(mock_db)
        
        # Kiểm tra xem phương thức index_text_content đã được gọi chưa
        mock_ci.index_text_content.assert_called()

if __name__ == '__main__':
    unittest.main()