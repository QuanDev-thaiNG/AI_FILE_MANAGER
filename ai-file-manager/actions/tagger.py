import sqlite3
from pathlib import Path

class FileTagger:
    """Lớp xử lý việc gắn thẻ cho các tập tin"""
    
    def __init__(self, db):
        """Khởi tạo với kết nối database"""
        self.db = db
    
    def add_tag(self, file_path, tag_name):
        """Thêm thẻ cho file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        # Lấy thông tin file từ database
        file_info = self.db.get_file_by_path(str(file_path))
        if not file_info:
            raise ValueError(f"File chưa được đăng ký trong database: {file_path}")
        
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
        
        # Kiểm tra xem liên kết file-tag đã tồn tại chưa
        cursor.execute(
            "SELECT * FROM file_tags WHERE file_id = ? AND tag_id = ?",
            (file_info['id'], tag_id))
        if cursor.fetchone():
            return {'success': True, 'message': f"Tag '{tag_name}' đã tồn tại cho file này"}
        
        # Thêm liên kết file-tag
        try:
            cursor.execute(
                "INSERT INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                (file_info['id'], tag_id))
            self.db.conn.commit()
            
            # Ghi log
            self.db.log_action(
                file_info['id'], 'add_tag', str(file_path), f"Added tag: {tag_name}")
            
            return {'success': True, 'message': f"Đã thêm tag '{tag_name}' cho file"}
        except Exception as e:
            self.db.conn.rollback()
            return {'success': False, 'error': str(e)}
    
    def remove_tag(self, file_path, tag_name):
        """Xóa thẻ khỏi file"""
        file_path = Path(file_path)
        
        # Lấy thông tin file từ database
        file_info = self.db.get_file_by_path(str(file_path))
        if not file_info:
            raise ValueError(f"File chưa được đăng ký trong database: {file_path}")
        
        # Lấy ID của tag
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        tag = cursor.fetchone()
        
        if not tag:
            return {'success': False, 'error': f"Tag '{tag_name}' không tồn tại"}
        
        # Xóa liên kết file-tag
        try:
            cursor.execute(
                "DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?",
                (file_info['id'], tag['id']))
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': f"File không có tag '{tag_name}'"}
            
            self.db.conn.commit()
            
            # Ghi log
            self.db.log_action(
                file_info['id'], 'remove_tag', str(file_path), f"Removed tag: {tag_name}")
            
            # Xóa tag nếu không còn file nào sử dụng
            cursor.execute(
                "SELECT COUNT(*) as count FROM file_tags WHERE tag_id = ?",
                (tag['id'],))
            count = cursor.fetchone()['count']
            
            if count == 0:
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag['id'],))
                self.db.conn.commit()
            
            return {'success': True, 'message': f"Đã xóa tag '{tag_name}' khỏi file"}
        except Exception as e:
            self.db.conn.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_file_tags(self, file_path):
        """Lấy danh sách thẻ của file"""
        file_path = Path(file_path)
        
        # Lấy thông tin file từ database
        file_info = self.db.get_file_by_path(str(file_path))
        if not file_info:
            raise ValueError(f"File chưa được đăng ký trong database: {file_path}")
        
        # Lấy danh sách tag
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT t.name 
               FROM tags t 
               JOIN file_tags ft ON t.id = ft.tag_id 
               WHERE ft.file_id = ? 
               ORDER BY t.name""",
            (file_info['id'],))
        
        tags = [row['name'] for row in cursor.fetchall()]
        return tags
    
    def get_files_by_tag(self, tag_name):
        """Lấy danh sách file có thẻ cụ thể"""
        # Lấy ID của tag
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        tag = cursor.fetchone()
        
        if not tag:
            return []
        
        # Lấy danh sách file
        cursor.execute(
            """SELECT f.id, f.abs_path, f.filename, f.size, f.created_at, f.modified_at, f.hash 
               FROM files f 
               JOIN file_tags ft ON f.id = ft.file_id 
               WHERE ft.tag_id = ? 
               ORDER BY f.filename""",
            (tag['id'],))
        
        files = [dict(row) for row in cursor.fetchall()]
        return files
    
    def get_all_tags(self):
        """Lấy danh sách tất cả các thẻ"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT t.name, COUNT(ft.file_id) as file_count 
               FROM tags t 
               LEFT JOIN file_tags ft ON t.id = ft.tag_id 
               GROUP BY t.id 
               ORDER BY t.name"""
        )
        
        tags = [dict(row) for row in cursor.fetchall()]
        return tags
    
    def auto_tag_by_rules(self, file_info, rules_engine):
        """Tự động gắn thẻ dựa trên quy tắc"""
        if not file_info or not rules_engine:
            return []
        
        # Lấy đường dẫn file
        file_path = file_info['abs_path']
        
        # Áp dụng quy tắc
        action_plan = rules_engine.apply_rules(file_info)
        if not action_plan or 'tags' not in action_plan:
            return []
        
        # Thêm các thẻ
        added_tags = []
        for tag_name in action_plan['tags']:
            result = self.add_tag(file_path, tag_name)
            if result['success']:
                added_tags.append(tag_name)
        
        return added_tags