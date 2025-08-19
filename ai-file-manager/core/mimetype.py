import mimetypes
from pathlib import Path

try:
    import magic
except ImportError:
    from core.magic_wrapper import detect_mime_type

class MimeTypeDetector:
    """Lớp phát hiện và phân loại MIME type của file"""
    
    def __init__(self):
        # Đảm bảo mimetypes đã được khởi tạo
        mimetypes.init()
    
    def detect_from_file(self, file_path):
        """Phát hiện MIME type từ nội dung file sử dụng python-magic"""
        try:
            # Thử sử dụng thư viện magic nếu đã import thành công
            if 'magic' in globals():
                return magic.from_file(str(file_path), mime=True)
            else:
                # Sử dụng magic_wrapper nếu không có thư viện magic
                return detect_mime_type(str(file_path))
        except Exception as e:
            print(f"Lỗi khi phát hiện MIME từ nội dung: {e}")
            # Fallback: sử dụng phương pháp dựa trên đuôi file
            return self.detect_from_extension(file_path)
    
    def detect_from_extension(self, file_path):
        """Phát hiện MIME type dựa trên đuôi file"""
        path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or "application/octet-stream"
    
    def get_category(self, mime_type):
        """Phân loại MIME type thành các nhóm chính"""
        if not mime_type:
            return "unknown"
        
        main_type = mime_type.split('/')[0]
        
        if main_type == "image":
            return "image"
        elif main_type == "video":
            return "video"
        elif main_type == "audio":
            return "audio"
        elif main_type == "text":
            return "text"
        elif mime_type in ["application/pdf"]:
            return "document"
        elif mime_type in ["application/msword", 
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          "application/vnd.oasis.opendocument.text"]:
            return "document"
        elif mime_type in ["application/vnd.ms-excel",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          "application/vnd.oasis.opendocument.spreadsheet"]:
            return "spreadsheet"
        elif mime_type in ["application/vnd.ms-powerpoint",
                          "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                          "application/vnd.oasis.opendocument.presentation"]:
            return "presentation"
        elif mime_type in ["application/zip", "application/x-rar-compressed", 
                          "application/x-tar", "application/gzip"]:
            return "archive"
        else:
            return "other"
    
    def is_processable(self, mime_type):
        """Kiểm tra xem file có thể được xử lý bởi hệ thống không"""
        processable_types = [
            "image/", "video/", "audio/", "text/",
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "application/vnd.oasis.opendocument"
        ]
        
        return any(mime_type.startswith(t) for t in processable_types)