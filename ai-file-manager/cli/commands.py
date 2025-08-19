import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

# Thêm thư mục gốc vào sys.path để import các module khác
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ingest import FileIngestor
from core.db import Database
from core.mimetype import MimeTypeDetector
from extractors.images import ImageExtractor
from extractors.pdfs import PDFExtractor
from extractors.videos import VideoExtractor
from rules.engine import RulesEngine
from rules.schemas import get_rule_template
from actions.mover import FileMover
from actions.tagger import FileTagger
from search.indexer import ContentIndexer
from search.searcher import FileSearcher

class CommandHandler:
    """Lớp xử lý các lệnh từ giao diện dòng lệnh"""
    
    def __init__(self):
        """Khởi tạo handler với các đối tượng cần thiết"""
        self.db_path = None
        self.db = None
        self.ingestor = None
        self.rules_engine = None
        self.file_mover = None
        self.file_tagger = None
        self.content_indexer = None
        self.file_searcher = None
    
    def setup(self, db_path: str):
        """Thiết lập các đối tượng cần thiết"""
        self.db_path = db_path
        self.db = Database(db_path)
        self.db.init_db()
        
        self.ingestor = FileIngestor(self.db)
        self.rules_engine = RulesEngine()
        self.file_mover = FileMover(self.db)
        self.file_tagger = FileTagger(self.db)
        self.content_indexer = ContentIndexer(self.db)
        self.file_searcher = FileSearcher(self.db)
    
    def ingest_command(self, args):
        """Xử lý lệnh ingest"""
        if not self.db or not self.ingestor:
            self.setup(args.db_path)
        
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"Lỗi: Đường dẫn nguồn không tồn tại: {source_path}")
            return 1
        
        print(f"Đang quét và đăng ký file từ: {source_path}")
        
        if source_path.is_file():
            result = self.ingestor.ingest_file(str(source_path))
            if result:
                print(f"Đã đăng ký file: {source_path}")
            else:
                print(f"Lỗi khi đăng ký file: {source_path}")
        else:
            count = self.ingestor.ingest_directory(
                str(source_path), 
                recursive=args.recursive, 
                dry_run=args.dry_run
            )
            print(f"Đã đăng ký {count} file từ {source_path}")
        
        return 0
    
    def organize_command(self, args):
        """Xử lý lệnh organize"""
        if not self.db or not self.rules_engine or not self.file_mover:
            self.setup(args.db_path)
        
        # Tải quy tắc từ file
        rules_path = Path(args.rules)
        if not rules_path.exists():
            print(f"Lỗi: File quy tắc không tồn tại: {rules_path}")
            return 1
        
        print(f"Đang tải quy tắc từ: {rules_path}")
        self.rules_engine.load_rules(str(rules_path))
        
        # Lấy danh sách file cần tổ chức
        cursor = self.db.conn.cursor()
        if args.source:
            source_path = Path(args.source)
            if source_path.is_file():
                cursor.execute(
                    "SELECT * FROM files WHERE abs_path = ?",
                    (str(source_path),))
            else:
                cursor.execute(
                    "SELECT * FROM files WHERE abs_path LIKE ?",
                    (f"{str(source_path)}%",))
        else:
            cursor.execute("SELECT * FROM files")
        
        files = cursor.fetchall()
        print(f"Tìm thấy {len(files)} file để tổ chức")
        
        # Áp dụng quy tắc và thực hiện hành động
        success_count = 0
        error_count = 0
        
        for file_info in files:
            file_info = dict(file_info)
            action_plans = self.rules_engine.apply_rules(file_info)
            
            if not action_plans:
                continue
            
            # Xử lý từng action plan trong danh sách
            for action_plan in action_plans:
                action = action_plan.get('action')
                if not action:
                    continue
                    
                result = self.file_mover.execute_action_plan(action, dry_run=args.dry_run)
            
                if result and result.get('success'):
                    success_count += 1
                    if args.verbose:
                        print(f"Thành công: {result['action_type']}: {result['source']} -> {result['target']}")
                else:
                    error_count += 1
                    if args.verbose or args.show_errors:
                        print(f"Lỗi: {result.get('error', 'Không rõ')} - {result.get('source')}")
        
        print(f"Kết quả: {success_count} thành công, {error_count} lỗi")
        return 0
    
    def search_command(self, args):
        """Xử lý lệnh search"""
        if not self.db or not self.file_searcher:
            self.setup(args.db_path)
        
        results = []
        
        # Tìm kiếm theo các tiêu chí khác nhau
        if args.filename:
            results = self.file_searcher.search_by_filename(args.filename, args.case_sensitive)
        elif args.extension:
            results = self.file_searcher.search_by_extension(args.extension)
        elif args.mimetype:
            results = self.file_searcher.search_by_mimetype(args.mimetype)
        elif args.tag:
            results = self.file_searcher.search_by_tag(args.tag)
        elif args.duplicates:
            duplicate_groups = self.file_searcher.search_duplicates(by_content=True)
            print(f"Tìm thấy {len(duplicate_groups)} nhóm file trùng lặp:")
            
            for i, group in enumerate(duplicate_groups):
                print(f"\nNhóm {i+1} ({len(group)} file):")
                for file in group:
                    print(f"  {file['abs_path']} ({file['size']} bytes)")
            
            return 0
        elif args.content and args.vector_search:
            # Tìm kiếm vector
            if not self.content_indexer:
                self.content_indexer = ContentIndexer(self.db)
            
            # Xây dựng chỉ mục nếu cần
            if args.rebuild_index:
                print("Đang tạo embedding...")
                self.content_indexer.create_embeddings(rebuild=True)
                print("Đang xây dựng chỉ mục FAISS...")
                self.content_indexer.build_faiss_index()
            
            print(f"Đang tìm kiếm: {args.content}")
            results = self.content_indexer.search(args.content, top_k=args.limit)
            
            # Hiển thị kết quả
            print(f"Tìm thấy {len(results)} kết quả:")
            for i, result in enumerate(results):
                print(f"\n{i+1}. {result['filename']} (Điểm số: {result['score']:.4f})")
                print(f"   Đường dẫn: {result['file_path']}")
                if args.show_content:
                    print(f"   Nội dung: {result['content'][:200]}...")
            
            return 0
        elif args.content:
            # Tìm kiếm từ khóa trong nội dung
            cursor = self.db.conn.cursor()
            cursor.execute(
                """SELECT f.* 
                   FROM files f 
                   JOIN content_index ci ON f.id = ci.file_id 
                   WHERE ci.content LIKE ? 
                   LIMIT ?""",
                (f"%{args.content}%", args.limit))
            
            results = [dict(row) for row in cursor.fetchall()]
        else:
            # Tìm kiếm kết hợp
            criteria = {}
            if args.min_size:
                criteria['min_size'] = args.min_size
            if args.max_size:
                criteria['max_size'] = args.max_size
            if args.start_date:
                criteria['start_date'] = args.start_date
            if args.end_date:
                criteria['end_date'] = args.end_date
            
            if criteria:
                results = self.file_searcher.search_by_multiple_criteria(criteria)
            else:
                print("Lỗi: Vui lòng cung cấp ít nhất một tiêu chí tìm kiếm")
                return 1
        
        # Hiển thị kết quả
        print(f"Tìm thấy {len(results)} kết quả:")
        for i, file in enumerate(results[:args.limit]):
            print(f"{i+1}. {file['filename']} ({file['size']} bytes)")
            print(f"   Đường dẫn: {file['abs_path']}")
            print(f"   Ngày tạo: {file['created_ts']}")
            
            if args.show_tags and self.file_tagger:
                tags = self.file_tagger.get_file_tags(file['abs_path'])
                if tags:
                    print(f"   Tags: {', '.join(tags)}")
            
            print()
        
        return 0
    
    def tag_command(self, args):
        """Xử lý lệnh tag"""
        if not self.db or not self.file_tagger:
            self.setup(args.db_path)
        
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Lỗi: File không tồn tại: {file_path}")
            return 1
        
        if args.add:
            result = self.file_tagger.add_tag(str(file_path), args.add)
            if result['success']:
                print(result['message'])
            else:
                print(f"Lỗi: {result.get('error', 'Không rõ')}")
        
        elif args.remove:
            result = self.file_tagger.remove_tag(str(file_path), args.remove)
            if result['success']:
                print(result['message'])
            else:
                print(f"Lỗi: {result.get('error', 'Không rõ')}")
        
        elif args.list:
            tags = self.file_tagger.get_file_tags(str(file_path))
            if tags:
                print(f"Tags của file {file_path.name}:")
                for tag in tags:
                    print(f"  - {tag}")
            else:
                print(f"File {file_path.name} không có tag nào")
        
        elif args.list_all:
            tags = self.file_tagger.get_all_tags()
            if tags:
                print("Danh sách tất cả các tag:")
                for tag in tags:
                    print(f"  - {tag['name']} ({tag['file_count']} file)")
            else:
                print("Không có tag nào trong hệ thống")
        
        return 0
    
    def index_command(self, args):
        """Xử lý lệnh index"""
        if not self.db or not self.content_indexer:
            self.setup(args.db_path)
        
        if args.rebuild:
            print("Đang tạo lại chỉ mục nội dung...")
            
            # Lấy danh sách file cần đánh chỉ mục
            cursor = self.db.conn.cursor()
            cursor.execute(
                """SELECT f.id, f.abs_path, f.filename, f.mime_type 
                   FROM files f 
                   WHERE f.mime_type LIKE 'text/%' 
                   OR f.mime_type LIKE 'application/pdf'"""
            )
            
            files = cursor.fetchall()
            print(f"Tìm thấy {len(files)} file văn bản để đánh chỉ mục")
            
            # Đánh chỉ mục từng file
            for i, file in enumerate(files):
                file_path = file['abs_path']
                file_id = file['id']
                mime_type = file['mime_type']
                
                print(f"Đang đánh chỉ mục ({i+1}/{len(files)}): {file_path}")
                
                try:
                    # Trích xuất nội dung
                    content = None
                    if mime_type.startswith('text/'):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    elif mime_type == 'application/pdf':
                        pdf_extractor = PDFExtractor()
                        content = pdf_extractor.extract_text(file_path)
                    
                    if content:
                        # Đánh chỉ mục nội dung
                        self.content_indexer.index_text_content(file_id, content)
                except Exception as e:
                    print(f"Lỗi khi đánh chỉ mục {file_path}: {e}")
            
            # Tạo embedding
            print("Đang tạo embedding...")
            self.content_indexer.create_embeddings(rebuild=True)
            
            # Xây dựng chỉ mục FAISS
            print("Đang xây dựng chỉ mục FAISS...")
            self.content_indexer.build_faiss_index()
            
            print("Hoàn thành đánh chỉ mục")
        
        elif args.status:
            # Hiển thị trạng thái chỉ mục
            cursor = self.db.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM content_index")
            content_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM embeddings")
            embedding_count = cursor.fetchone()['count']
            
            print("Trạng thái chỉ mục:")
            print(f"  - Số đoạn văn bản đã đánh chỉ mục: {content_count}")
            print(f"  - Số embedding đã tạo: {embedding_count}")
        
        return 0
    
    def init_command(self, args):
        """Xử lý lệnh init"""
        # Tạo thư mục cấu hình nếu chưa tồn tại
        config_dir = Path(args.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Tạo file cấu hình mẫu
        config_path = config_dir / "config.yaml"
        if not config_path.exists() or args.force:
            config = {
                "database": {
                    "path": str(config_dir / "filemanager.db")
                },
                "rules_dir": str(config_dir / "rules"),
                "default_rules": str(config_dir / "rules" / "default.yaml"),
                "temp_dir": str(config_dir / "temp"),
                "log_file": str(config_dir / "filemanager.log"),
                "extractors": {
                    "image": {
                        "use_exif": True,
                        "use_ocr": False,
                        "ocr_language": "vie+eng"
                    },
                    "pdf": {
                        "extract_text": True,
                        "extract_images": False,
                        "use_ocr": False,
                        "ocr_language": "vie+eng"
                    },
                    "video": {
                        "extract_frames": False,
                        "frame_interval": 10,
                        "extract_audio": False
                    }
                },
                "indexing": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"Đã tạo file cấu hình mẫu: {config_path}")
        
        # Tạo thư mục quy tắc
        rules_dir = config_dir / "rules"
        rules_dir.mkdir(exist_ok=True)
        
        # Tạo file quy tắc mẫu
        default_rules_path = rules_dir / "default.yaml"
        if not default_rules_path.exists() or args.force:
            template = get_rule_template()
            
            with open(default_rules_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"Đã tạo file quy tắc mẫu: {default_rules_path}")
        
        # Tạo thư mục temp
        temp_dir = config_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Khởi tạo database
        db_path = config_dir / "filemanager.db"
        if not db_path.exists() or args.force:
            db = Database(str(db_path))
            db.init_db()
            print(f"Đã khởi tạo database: {db_path}")
        
        print(f"Khởi tạo hoàn tất. Sử dụng thư mục cấu hình: {config_dir}")
        return 0

def main():
    """Hàm chính xử lý giao diện dòng lệnh"""
    # Tạo parser chính
    parser = argparse.ArgumentParser(
        description="Công cụ quản lý và sắp xếp tập tin thông minh",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Thêm các tham số chung
    parser.add_argument(
        "--db-path", 
        default=os.path.expanduser("~/.filemanager/filemanager.db"),
        help="Đường dẫn đến file database"
    )
    
    # Tạo các subparser cho các lệnh
    subparsers = parser.add_subparsers(dest="command", help="Lệnh cần thực hiện")
    
    # Lệnh init
    init_parser = subparsers.add_parser("init", help="Khởi tạo cấu hình và database")
    init_parser.add_argument(
        "--config-dir", 
        default=os.path.expanduser("~/.filemanager"),
        help="Thư mục cấu hình"
    )
    init_parser.add_argument(
        "--force", 
        action="store_true",
        help="Ghi đè các file đã tồn tại"
    )
    
    # Lệnh ingest
    ingest_parser = subparsers.add_parser("ingest", help="Quét và đăng ký file")
    ingest_parser.add_argument(
        "source",
        help="Đường dẫn đến file hoặc thư mục nguồn"
    )
    ingest_parser.add_argument(
        "--recursive", 
        "-r",
        action="store_true",
        help="Quét đệ quy các thư mục con"
    )
    ingest_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị kế hoạch, không thực hiện thay đổi"
    )
    
    # Lệnh organize
    organize_parser = subparsers.add_parser("organize", help="Tổ chức file theo quy tắc")
    organize_parser.add_argument(
        "--rules",
        default=os.path.expanduser("~/.filemanager/rules/default.yaml"),
        help="Đường dẫn đến file quy tắc"
    )
    organize_parser.add_argument(
        "--source",
        help="Đường dẫn đến file hoặc thư mục nguồn (tùy chọn)"
    )
    organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị kế hoạch, không thực hiện thay đổi"
    )
    organize_parser.add_argument(
        "--verbose", 
        "-v",
        action="store_true",
        help="Hiển thị thông tin chi tiết"
    )
    organize_parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Chỉ hiển thị các lỗi"
    )
    
    # Lệnh search
    search_parser = subparsers.add_parser("search", help="Tìm kiếm file")
    search_parser.add_argument(
        "--filename",
        help="Tìm kiếm theo tên file"
    )
    search_parser.add_argument(
        "--extension",
        help="Tìm kiếm theo phần mở rộng"
    )
    search_parser.add_argument(
        "--mimetype",
        help="Tìm kiếm theo loại MIME"
    )
    search_parser.add_argument(
        "--tag",
        help="Tìm kiếm theo thẻ"
    )
    search_parser.add_argument(
        "--content",
        help="Tìm kiếm theo nội dung"
    )
    search_parser.add_argument(
        "--vector-search",
        action="store_true",
        help="Sử dụng tìm kiếm vector cho nội dung"
    )
    search_parser.add_argument(
        "--min-size",
        type=int,
        help="Kích thước tối thiểu (bytes)"
    )
    search_parser.add_argument(
        "--max-size",
        type=int,
        help="Kích thước tối đa (bytes)"
    )
    search_parser.add_argument(
        "--start-date",
        help="Ngày bắt đầu (YYYY-MM-DD)"
    )
    search_parser.add_argument(
        "--end-date",
        help="Ngày kết thúc (YYYY-MM-DD)"
    )
    search_parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Tìm kiếm các file trùng lặp"
    )
    search_parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Tìm kiếm phân biệt chữ hoa/thường"
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Số lượng kết quả tối đa"
    )
    search_parser.add_argument(
        "--show-tags",
        action="store_true",
        help="Hiển thị các thẻ của file"
    )
    search_parser.add_argument(
        "--show-content",
        action="store_true",
        help="Hiển thị nội dung của file"
    )
    search_parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Xây dựng lại chỉ mục trước khi tìm kiếm"
    )
    
    # Lệnh tag
    tag_parser = subparsers.add_parser("tag", help="Quản lý thẻ cho file")
    tag_parser.add_argument(
        "--file",
        help="Đường dẫn đến file"
    )
    tag_parser.add_argument(
        "--add",
        help="Thêm thẻ cho file"
    )
    tag_parser.add_argument(
        "--remove",
        help="Xóa thẻ khỏi file"
    )
    tag_parser.add_argument(
        "--list",
        action="store_true",
        help="Liệt kê các thẻ của file"
    )
    tag_parser.add_argument(
        "--list-all",
        action="store_true",
        help="Liệt kê tất cả các thẻ trong hệ thống"
    )
    
    # Lệnh index
    index_parser = subparsers.add_parser("index", help="Quản lý chỉ mục nội dung")
    index_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Xây dựng lại chỉ mục nội dung"
    )
    index_parser.add_argument(
        "--status",
        action="store_true",
        help="Hiển thị trạng thái chỉ mục"
    )
    
    # Phân tích tham số
    args = parser.parse_args()
    
    # Xử lý lệnh
    handler = CommandHandler()
    
    if args.command == "init":
        return handler.init_command(args)
    elif args.command == "ingest":
        return handler.ingest_command(args)
    elif args.command == "organize":
        return handler.organize_command(args)
    elif args.command == "search":
        return handler.search_command(args)
    elif args.command == "tag":
        return handler.tag_command(args)
    elif args.command == "index":
        return handler.index_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())