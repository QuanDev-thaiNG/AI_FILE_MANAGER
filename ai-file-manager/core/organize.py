import os
import shutil
import json

class Organizer:
    def __init__(self, db):
        self.db = db
        
    def organize(self, source_dir, rule_name, dry_run=False):
        """Tổ chức tập tin theo quy tắc được chỉ định
        
        Args:
            source_dir (str): Thư mục nguồn chứa các tập tin cần tổ chức
            rule_name (str): Tên quy tắc tổ chức (by_type, by_date, by_extension, by_size, by_content)
            dry_run (bool): Nếu True, chỉ mô phỏng quá trình tổ chức mà không thực sự di chuyển tập tin
            
        Returns:
            list: Danh sách kết quả tổ chức tập tin
        """
        # Tạo thư mục đích nếu đang trong chế độ thực thi (không phải dry run)
        target_dir = source_dir
        if not dry_run:
            target_dir = os.path.join(source_dir, f"organized_{rule_name}")
            
        # Gọi phương thức tổ chức tương ứng dựa trên rule_name
        if rule_name == "by_type":
            success, message = self.organize_by_type(source_dir, target_dir)
        elif rule_name == "by_date":
            success, message = self.organize_by_date(source_dir, target_dir)
        elif rule_name == "by_extension":
            success, message = self.organize_by_extension(source_dir, target_dir)
        elif rule_name == "by_size":
            return [{"source": source_dir, "target": target_dir, "status": "error", "message": "Chức năng tổ chức theo kích thước chưa được triển khai"}]
        elif rule_name == "by_content":
            return [{"source": source_dir, "target": target_dir, "status": "error", "message": "Chức năng tổ chức theo nội dung chưa được triển khai"}]
        else:
            return [{"source": source_dir, "target": target_dir, "status": "error", "message": f"Quy tắc tổ chức không hợp lệ: {rule_name}"}]
        
        # Trả về kết quả
        if success:
            return [{"source": source_dir, "target": target_dir, "status": "success", "message": message}]
        else:
            return [{"source": source_dir, "target": target_dir, "status": "error", "message": message}]
    
    def organize_by_extension(self, source_dir, target_dir):
        """
        Tổ chức tập tin theo phần mở rộng
        """
        try:
            if not os.path.exists(source_dir):
                return False, "Thư mục nguồn không tồn tại"
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Lấy danh sách tập tin từ thư mục nguồn
            files_moved = 0
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, extension = os.path.splitext(file)
                    
                    # Bỏ qua nếu không có phần mở rộng
                    if not extension:
                        continue
                    
                    # Tạo thư mục cho phần mở rộng (bỏ dấu chấm)
                    extension_dir = os.path.join(target_dir, extension[1:].lower())
                    if not os.path.exists(extension_dir):
                        os.makedirs(extension_dir)
                    
                    # Di chuyển tập tin
                    target_path = os.path.join(extension_dir, file)
                    if os.path.exists(target_path):
                        base, ext = os.path.splitext(file)
                        i = 1
                        while os.path.exists(os.path.join(extension_dir, f"{base}_{i}{ext}")):
                            i += 1
                        target_path = os.path.join(extension_dir, f"{base}_{i}{ext}")
                    
                    shutil.move(file_path, target_path)
                    files_moved += 1
                    
                    # Cập nhật đường dẫn trong cơ sở dữ liệu
                    if self.db.conn:
                        self.db.execute_query(
                            "UPDATE files SET path = ? WHERE path = ?",
                            (target_path, file_path)
                        )
            
            return True, f"Đã di chuyển {files_moved} tập tin"
        except Exception as e:
            return False, f"Lỗi khi tổ chức tập tin: {e}"
    
    def organize_by_date(self, source_dir, target_dir, date_format='year_month'):
        """
        Tổ chức tập tin theo ngày tạo
        date_format: 'year_month' hoặc 'year'
        """
        try:
            if not os.path.exists(source_dir):
                return False, "Thư mục nguồn không tồn tại"
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Lấy danh sách tập tin từ thư mục nguồn
            files_moved = 0
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Lấy thông tin tập tin từ cơ sở dữ liệu
                    if self.db.conn:
                        file_info = self.db.fetch_query(
                            "SELECT created_date FROM files WHERE path = ?",
                            (file_path,)
                        )
                        
                        if file_info and file_info[0][0]:
                            created_date = file_info[0][0]
                            year, month, _ = created_date.split('-')
                            
                            # Tạo thư mục theo định dạng ngày
                            if date_format == 'year_month':
                                date_dir = os.path.join(target_dir, year, month)
                            else:  # year
                                date_dir = os.path.join(target_dir, year)
                            
                            if not os.path.exists(date_dir):
                                os.makedirs(date_dir)
                            
                            # Di chuyển tập tin
                            target_path = os.path.join(date_dir, file)
                            if os.path.exists(target_path):
                                base, ext = os.path.splitext(file)
                                i = 1
                                while os.path.exists(os.path.join(date_dir, f"{base}_{i}{ext}")):
                                    i += 1
                                target_path = os.path.join(date_dir, f"{base}_{i}{ext}")
                            
                            shutil.move(file_path, target_path)
                            files_moved += 1
                            
                            # Cập nhật đường dẫn trong cơ sở dữ liệu
                            self.db.execute_query(
                                "UPDATE files SET path = ? WHERE path = ?",
                                (target_path, file_path)
                            )
            
            return True, f"Đã di chuyển {files_moved} tập tin"
        except Exception as e:
            return False, f"Lỗi khi tổ chức tập tin: {e}"
    
    def organize_by_type(self, source_dir, target_dir):
        """
        Tổ chức tập tin theo loại (hình ảnh, văn bản, video, âm thanh, tài liệu)
        """
        try:
            if not os.path.exists(source_dir):
                return False, "Thư mục nguồn không tồn tại"
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Định nghĩa các loại tập tin
            file_types = {
                'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
                'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt'],
                'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma'],
                'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.ts']
            }
            
            # Tạo thư mục cho từng loại
            for type_dir in file_types.keys():
                os.makedirs(os.path.join(target_dir, type_dir), exist_ok=True)
            
            # Thư mục cho các loại không xác định
            os.makedirs(os.path.join(target_dir, 'others'), exist_ok=True)
            
            # Lấy danh sách tập tin từ thư mục nguồn
            files_moved = 0
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, extension = os.path.splitext(file)
                    extension = extension.lower()
                    
                    # Xác định loại tập tin
                    file_type = 'others'
                    for type_name, extensions in file_types.items():
                        if extension in extensions:
                            file_type = type_name
                            break
                    
                    # Tạo thư mục đích
                    type_dir = os.path.join(target_dir, file_type)
                    
                    # Di chuyển tập tin
                    target_path = os.path.join(type_dir, file)
                    if os.path.exists(target_path):
                        base, ext = os.path.splitext(file)
                        i = 1
                        while os.path.exists(os.path.join(type_dir, f"{base}_{i}{ext}")):
                            i += 1
                        target_path = os.path.join(type_dir, f"{base}_{i}{ext}")
                    
                    shutil.move(file_path, target_path)
                    files_moved += 1
                    
                    # Cập nhật đường dẫn trong cơ sở dữ liệu
                    if self.db.conn:
                        self.db.execute_query(
                            "UPDATE files SET path = ? WHERE path = ?",
                            (target_path, file_path)
                        )
            
            return True, f"Đã di chuyển {files_moved} tập tin"
        except Exception as e:
            return False, f"Lỗi khi tổ chức tập tin: {e}"