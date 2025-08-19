import os
import shutil
from pathlib import Path
import hashlib

class FileMover:
    """Lớp thực hiện các thao tác di chuyển, sao chép, đổi tên và liên kết file"""
    
    def __init__(self, db=None):
        """Khởi tạo với kết nối database (tùy chọn)"""
        self.db = db
    
    def move_file(self, source, target, verify=True):
        """Di chuyển file từ source đến target"""
        source_path = Path(source)
        target_path = Path(target)
        
        if not source_path.exists():
            raise FileNotFoundError(f"File nguồn không tồn tại: {source}")
        
        # Tạo thư mục đích nếu chưa tồn tại
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Kiểm tra xem file đích đã tồn tại chưa
        if target_path.exists():
            raise FileExistsError(f"File đích đã tồn tại: {target}")
        
        # Tính hash trước khi di chuyển nếu cần xác minh
        source_hash = None
        if verify:
            source_hash = self._calculate_hash(source_path)
        
        # Di chuyển file
        try:
            shutil.move(str(source_path), str(target_path))
        except Exception as e:
            raise RuntimeError(f"Lỗi khi di chuyển file: {e}")
        
        # Xác minh hash sau khi di chuyển
        if verify and source_hash:
            target_hash = self._calculate_hash(target_path)
            if source_hash != target_hash:
                # Nếu hash không khớp, thử khôi phục file nguồn
                try:
                    shutil.move(str(target_path), str(source_path))
                except Exception:
                    pass
                raise RuntimeError(f"Lỗi xác minh hash sau khi di chuyển: {source} -> {target}")
        
        # Ghi log vào database nếu có
        if self.db:
            file_info = self.db.get_file_by_path(str(source_path))
            if file_info:
                action_id = self.db.log_action(
                    file_info['id'], 'move', str(source_path), str(target_path))
                
                # Cập nhật đường dẫn trong database
                self.db.conn.execute(
                    "UPDATE files SET abs_path = ? WHERE id = ?",
                    (str(target_path), file_info['id']))
                self.db.conn.commit()
        
        return str(target_path)
    
    def copy_file(self, source, target, verify=True):
        """Sao chép file từ source đến target"""
        source_path = Path(source)
        target_path = Path(target)
        
        if not source_path.exists():
            raise FileNotFoundError(f"File nguồn không tồn tại: {source}")
        
        # Tạo thư mục đích nếu chưa tồn tại
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Kiểm tra xem file đích đã tồn tại chưa
        if target_path.exists():
            raise FileExistsError(f"File đích đã tồn tại: {target}")
        
        # Tính hash trước khi sao chép nếu cần xác minh
        source_hash = None
        if verify:
            source_hash = self._calculate_hash(source_path)
        
        # Sao chép file
        try:
            shutil.copy2(str(source_path), str(target_path))
        except Exception as e:
            raise RuntimeError(f"Lỗi khi sao chép file: {e}")
        
        # Xác minh hash sau khi sao chép
        if verify and source_hash:
            target_hash = self._calculate_hash(target_path)
            if source_hash != target_hash:
                # Nếu hash không khớp, xóa file đích
                try:
                    os.remove(str(target_path))
                except Exception:
                    pass
                raise RuntimeError(f"Lỗi xác minh hash sau khi sao chép: {source} -> {target}")
        
        # Ghi log vào database nếu có
        if self.db:
            file_info = self.db.get_file_by_path(str(source_path))
            if file_info:
                self.db.log_action(
                    file_info['id'], 'copy', str(source_path), str(target_path))
        
        return str(target_path)
    
    def rename_file(self, source, new_name, verify=True):
        """Đổi tên file"""
        source_path = Path(source)
        target_path = source_path.parent / new_name
        
        if not source_path.exists():
            raise FileNotFoundError(f"File nguồn không tồn tại: {source}")
        
        # Kiểm tra xem file đích đã tồn tại chưa
        if target_path.exists():
            raise FileExistsError(f"File đích đã tồn tại: {target_path}")
        
        # Tính hash trước khi đổi tên nếu cần xác minh
        source_hash = None
        if verify:
            source_hash = self._calculate_hash(source_path)
        
        # Đổi tên file
        try:
            os.rename(str(source_path), str(target_path))
        except Exception as e:
            raise RuntimeError(f"Lỗi khi đổi tên file: {e}")
        
        # Xác minh hash sau khi đổi tên
        if verify and source_hash:
            target_hash = self._calculate_hash(target_path)
            if source_hash != target_hash:
                # Nếu hash không khớp, thử khôi phục tên cũ
                try:
                    os.rename(str(target_path), str(source_path))
                except Exception:
                    pass
                raise RuntimeError(f"Lỗi xác minh hash sau khi đổi tên: {source} -> {target_path}")
        
        # Ghi log vào database nếu có
        if self.db:
            file_info = self.db.get_file_by_path(str(source_path))
            if file_info:
                action_id = self.db.log_action(
                    file_info['id'], 'rename', str(source_path), str(target_path))
                
                # Cập nhật đường dẫn trong database
                self.db.conn.execute(
                    "UPDATE files SET abs_path = ?, filename = ? WHERE id = ?",
                    (str(target_path), target_path.name, file_info['id']))
                self.db.conn.commit()
        
        return str(target_path)
    
    def create_link(self, source, target, link_type='hard'):
        """Tạo liên kết (hard link hoặc symbolic link)"""
        source_path = Path(source)
        target_path = Path(target)
        
        if not source_path.exists():
            raise FileNotFoundError(f"File nguồn không tồn tại: {source}")
        
        # Tạo thư mục đích nếu chưa tồn tại
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Kiểm tra xem file đích đã tồn tại chưa
        if target_path.exists():
            raise FileExistsError(f"File đích đã tồn tại: {target}")
        
        # Tạo liên kết
        try:
            if link_type == 'hard':
                os.link(str(source_path), str(target_path))
            elif link_type == 'symbolic':
                os.symlink(str(source_path), str(target_path))
            else:
                raise ValueError(f"Loại liên kết không hợp lệ: {link_type}")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tạo liên kết {link_type}: {e}")
        
        # Ghi log vào database nếu có
        if self.db:
            file_info = self.db.get_file_by_path(str(source_path))
            if file_info:
                self.db.log_action(
                    file_info['id'], f'link_{link_type}', str(source_path), str(target_path))
        
        return str(target_path)
    
    def _calculate_hash(self, file_path):
        """Tính toán hash SHA-256 của file"""
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1<<20), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def execute_action_plan(self, action_plan, dry_run=False):
        """Thực thi kế hoạch hành động"""
        if not action_plan:
            return None
        
        source = action_plan['source']
        target = action_plan['target']
        action_type = action_plan['action_type']
        
        # Hiển thị kế hoạch nếu là dry run
        if dry_run:
            print(f"[DRY RUN] {action_type}: {source} -> {target}")
            return {
                'success': True,
                'source': source,
                'target': target,
                'action_type': action_type,
                'dry_run': True
            }
        
        # Thực thi hành động
        try:
            if action_type == 'move':
                result = self.move_file(source, target)
            elif action_type == 'copy':
                result = self.copy_file(source, target)
            elif action_type == 'rename':
                new_name = os.path.basename(target)
                result = self.rename_file(source, new_name)
            elif action_type == 'link':
                result = self.create_link(source, target)
            else:
                raise ValueError(f"Loại hành động không hợp lệ: {action_type}")
            
            # Thêm tags nếu có
            if self.db and 'tags' in action_plan:
                file_info = self.db.get_file_by_path(target)
                if file_info:
                    for tag_name in action_plan['tags']:
                        # Kiểm tra xem tag đã tồn tại chưa
                        cursor = self.db.conn.cursor()
                        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                        tag = cursor.fetchone()
                        
                        if not tag:
                            # Tạo tag mới
                            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                            tag_id = cursor.lastrowid
                        else:
                            tag_id = tag['id']
                        
                        # Thêm liên kết file-tag
                        try:
                            cursor.execute(
                                "INSERT INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                                (file_info['id'], tag_id))
                        except Exception:
                            # Bỏ qua nếu liên kết đã tồn tại
                            pass
                    
                    self.db.conn.commit()
            
            return {
                'success': True,
                'source': source,
                'target': result,
                'action_type': action_type
            }
        except Exception as e:
            return {
                'success': False,
                'source': source,
                'target': target,
                'action_type': action_type,
                'error': str(e)
            }