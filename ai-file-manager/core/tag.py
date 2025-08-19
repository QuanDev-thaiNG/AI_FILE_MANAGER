import os
import json

class TagManager:
    def __init__(self, db):
        self.db = db
    
    def add_tag(self, tag_name):
        """
        Thêm một tag mới
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Kiểm tra xem tag đã tồn tại chưa
            existing_tag = self.db.fetch_query(
                "SELECT id FROM tags WHERE name = ?",
                (tag_name,)
            )
            
            if existing_tag:
                return existing_tag[0][0]  # Trả về ID của tag đã tồn tại
            
            # Thêm tag mới
            self.db.execute_query(
                "INSERT INTO tags (name) VALUES (?)",
                (tag_name,)
            )
            
            # Lấy ID của tag vừa thêm
            tag_id = self.db.fetch_query(
                "SELECT id FROM tags WHERE name = ?",
                (tag_name,)
            )
            
            if tag_id:
                return tag_id[0][0]
            return None
        except Exception as e:
            print(f"Lỗi khi thêm tag: {e}")
            return None
    
    def remove_tag(self, tag_id):
        """
        Xóa một tag
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Xóa tag
            self.db.execute_query(
                "DELETE FROM tags WHERE id = ?",
                (tag_id,)
            )
            
            return True
        except Exception as e:
            print(f"Lỗi khi xóa tag: {e}")
            return False
    
    def get_all_tags(self):
        """
        Lấy danh sách tất cả các tag
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            tags = self.db.fetch_query("SELECT id, name FROM tags")
            
            return [{'id': tag[0], 'name': tag[1]} for tag in tags]
        except Exception as e:
            print(f"Lỗi khi lấy danh sách tag: {e}")
            return []
    
    def tag_file(self, file_id, tag_id):
        """
        Gán tag cho một tập tin
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Kiểm tra xem đã gán tag này cho file chưa
            existing = self.db.fetch_query(
                "SELECT * FROM file_tags WHERE file_id = ? AND tag_id = ?",
                (file_id, tag_id)
            )
            
            if existing:
                return True  # Đã gán tag này rồi
            
            # Gán tag cho file
            self.db.execute_query(
                "INSERT INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                (file_id, tag_id)
            )
            
            return True
        except Exception as e:
            print(f"Lỗi khi gán tag cho file: {e}")
            return False
    
    def untag_file(self, file_id, tag_id):
        """
        Gỡ tag khỏi một tập tin
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Gỡ tag khỏi file
            self.db.execute_query(
                "DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?",
                (file_id, tag_id)
            )
            
            return True
        except Exception as e:
            print(f"Lỗi khi gỡ tag khỏi file: {e}")
            return False
    
    def get_file_tags(self, file_id):
        """
        Lấy danh sách tag của một tập tin
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            tags = self.db.fetch_query(
                "SELECT t.id, t.name FROM tags t "
                "JOIN file_tags ft ON t.id = ft.tag_id "
                "WHERE ft.file_id = ?",
                (file_id,)
            )
            
            return [{'id': tag[0], 'name': tag[1]} for tag in tags]
        except Exception as e:
            print(f"Lỗi khi lấy danh sách tag của file: {e}")
            return []
    
    def get_files_by_tag(self, tag_id):
        """
        Lấy danh sách tập tin có tag cụ thể
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            files = self.db.fetch_query(
                "SELECT f.id, f.path, f.filename, f.extension, f.size, f.mime_type "
                "FROM files f "
                "JOIN file_tags ft ON f.id = ft.file_id "
                "WHERE ft.tag_id = ?",
                (tag_id,)
            )
            
            return [{
                'id': file[0],
                'path': file[1],
                'filename': file[2],
                'extension': file[3],
                'size': file[4],
                'mime_type': file[5]
            } for file in files]
        except Exception as e:
            print(f"Lỗi khi lấy danh sách file theo tag: {e}")
            return []