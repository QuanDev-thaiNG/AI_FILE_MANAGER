import os
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

class FileSearcher:
    """Lớp tìm kiếm file dựa trên các tiêu chí khác nhau"""
    
    def __init__(self, db):
        """Khởi tạo với kết nối database"""
        self.db = db
    
    def search_by_filename(self, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo tên file"""
        cursor = self.db.conn.cursor()
        
        if case_sensitive:
            cursor.execute(
                "SELECT * FROM files WHERE filename LIKE ? ORDER BY filename",
                (f"%{pattern}%",))
        else:
            cursor.execute(
                "SELECT * FROM files WHERE filename LIKE ? COLLATE NOCASE ORDER BY filename",
                (f"%{pattern}%",))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_extension(self, extension: str) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo phần mở rộng"""
        if extension.startswith('.'):
            extension = extension[1:]
        
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE filename LIKE ? ORDER BY filename",
            (f"%.{extension}",))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_mimetype(self, mimetype: str) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo loại MIME"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE mime_type LIKE ? ORDER BY filename",
            (f"{mimetype}%",))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_size(self, min_size: Optional[int] = None, max_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo kích thước (bytes)"""
        cursor = self.db.conn.cursor()
        
        if min_size is not None and max_size is not None:
            cursor.execute(
                "SELECT * FROM files WHERE size BETWEEN ? AND ? ORDER BY size",
                (min_size, max_size))
        elif min_size is not None:
            cursor.execute(
                "SELECT * FROM files WHERE size >= ? ORDER BY size",
                (min_size,))
        elif max_size is not None:
            cursor.execute(
                "SELECT * FROM files WHERE size <= ? ORDER BY size",
                (max_size,))
        else:
            cursor.execute("SELECT * FROM files ORDER BY size")
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_date(self, 
                      start_date: Optional[Union[str, datetime]] = None, 
                      end_date: Optional[Union[str, datetime]] = None,
                      date_type: str = 'created') -> List[Dict[str, Any]]:
        """Tìm kiếm file theo ngày tạo hoặc sửa đổi"""
        cursor = self.db.conn.cursor()
        
        # Chuyển đổi ngày thành chuỗi nếu cần
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Xác định trường ngày
        date_field = 'created_at' if date_type == 'created' else 'modified_at'
        
        if start_date is not None and end_date is not None:
            cursor.execute(
                f"SELECT * FROM files WHERE {date_field} BETWEEN ? AND ? ORDER BY {date_field}",
                (start_date, end_date))
        elif start_date is not None:
            cursor.execute(
                f"SELECT * FROM files WHERE {date_field} >= ? ORDER BY {date_field}",
                (start_date,))
        elif end_date is not None:
            cursor.execute(
                f"SELECT * FROM files WHERE {date_field} <= ? ORDER BY {date_field}",
                (end_date,))
        else:
            cursor.execute(f"SELECT * FROM files ORDER BY {date_field}")
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_hash(self, file_hash: str) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo hash"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE hash = ?",
            (file_hash,))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_tag(self, tag_name: str) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo thẻ"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT f.* 
               FROM files f 
               JOIN file_tags ft ON f.id = ft.file_id 
               JOIN tags t ON ft.tag_id = t.id 
               WHERE t.name = ? 
               ORDER BY f.filename""",
            (tag_name,))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_exif(self, exif_field: str, value: str) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo thông tin EXIF"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT f.* 
               FROM files f 
               JOIN metadata_media mm ON f.id = mm.file_id 
               WHERE mm.exif_data LIKE ? 
               ORDER BY f.filename""",
            (f"%\"{exif_field}\":\"{value}\"%",))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    
    def search_by_location(self, lat: float, lon: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo vị trí địa lý (cần thông tin GPS trong EXIF)"""
        # Chuyển đổi bán kính từ km sang độ (xấp xỉ)
        radius_deg = radius_km / 111.0  # 1 độ ~ 111 km
        
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT f.*, mm.gps_latitude, mm.gps_longitude 
               FROM files f 
               JOIN metadata_media mm ON f.id = mm.file_id 
               WHERE mm.gps_latitude IS NOT NULL AND mm.gps_longitude IS NOT NULL 
               ORDER BY f.filename"""
        )
        
        all_files = cursor.fetchall()
        results = []
        
        for file in all_files:
            file_lat = file['gps_latitude']
            file_lon = file['gps_longitude']
            
            if file_lat is None or file_lon is None:
                continue
            
            # Tính khoảng cách (xấp xỉ)
            distance = ((file_lat - lat) ** 2 + (file_lon - lon) ** 2) ** 0.5
            
            if distance <= radius_deg:
                file_dict = dict(file)
                file_dict['distance_km'] = distance * 111.0
                results.append(file_dict)
        
        # Sắp xếp theo khoảng cách
        results.sort(key=lambda x: x.get('distance_km', float('inf')))
        return results
    
    def search_duplicates(self, by_content: bool = True) -> List[List[Dict[str, Any]]]:
        """Tìm kiếm các file trùng lặp"""
        cursor = self.db.conn.cursor()
        
        if by_content:
            # Tìm kiếm theo hash nội dung
            cursor.execute(
                """SELECT hash_sha256, COUNT(*) as count 
                   FROM files 
                   WHERE hash_sha256 IS NOT NULL 
                   GROUP BY hash_sha256 
                   HAVING count > 1""")
            
            duplicate_hashes = [row['hash_sha256'] for row in cursor.fetchall()]
            
            duplicate_groups = []
            for file_hash in duplicate_hashes:
                cursor.execute(
                    "SELECT * FROM files WHERE hash_sha256 = ? ORDER BY filename",
                    (file_hash,))
                
                files = [dict(row) for row in cursor.fetchall()]
                duplicate_groups.append(files)
            
            return duplicate_groups
        else:
            # Tìm kiếm theo tên file
            cursor.execute(
                """SELECT filename, COUNT(*) as count 
                   FROM files 
                   GROUP BY filename 
                   HAVING count > 1""")
            
            duplicate_names = [row['filename'] for row in cursor.fetchall()]
            
            duplicate_groups = []
            for filename in duplicate_names:
                cursor.execute(
                    "SELECT * FROM files WHERE filename = ? ORDER BY abs_path",
                    (filename,))
                
                files = [dict(row) for row in cursor.fetchall()]
                duplicate_groups.append(files)
            
            return duplicate_groups
    
    def search_by_multiple_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tìm kiếm file theo nhiều tiêu chí kết hợp"""
        # Xây dựng truy vấn SQL
        query_parts = ["SELECT f.* FROM files f"]
        joins = []
        where_clauses = []
        params = []
        
        # Xử lý các tiêu chí
        if 'filename' in criteria:
            where_clauses.append("f.filename LIKE ? COLLATE NOCASE")
            params.append(f"%{criteria['filename']}%")
        
        if 'extension' in criteria:
            ext = criteria['extension']
            if ext.startswith('.'):
                ext = ext[1:]
            where_clauses.append("f.filename LIKE ?")
            params.append(f"%.{ext}")
        
        if 'mimetype' in criteria:
            where_clauses.append("f.mime_type LIKE ?")
            params.append(f"{criteria['mimetype']}%")
        
        if 'min_size' in criteria:
            where_clauses.append("f.size >= ?")
            params.append(criteria['min_size'])
        
        if 'max_size' in criteria:
            where_clauses.append("f.size <= ?")
            params.append(criteria['max_size'])
        
        if 'start_date' in criteria:
            date_field = 'f.created_at' if criteria.get('date_type', 'created') == 'created' else 'f.modified_at'
            where_clauses.append(f"{date_field} >= ?")
            params.append(criteria['start_date'])
        
        if 'end_date' in criteria:
            date_field = 'f.created_at' if criteria.get('date_type', 'created') == 'created' else 'f.modified_at'
            where_clauses.append(f"{date_field} <= ?")
            params.append(criteria['end_date'])
        
        if 'tag' in criteria:
            joins.append("JOIN file_tags ft ON f.id = ft.file_id")
            joins.append("JOIN tags t ON ft.tag_id = t.id")
            where_clauses.append("t.name = ?")
            params.append(criteria['tag'])
        
        if 'exif_field' in criteria and 'exif_value' in criteria:
            joins.append("JOIN metadata_media mm ON f.id = mm.file_id")
            where_clauses.append("mm.exif_data LIKE ?")
            params.append(f"%\"{criteria['exif_field']}\":\"{criteria['exif_value']}\"%")
        
        # Kết hợp các phần truy vấn
        if joins:
            query_parts.extend(joins)
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query_parts.append("ORDER BY f.filename")
        query = " ".join(query_parts)
        
        # Thực hiện truy vấn
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results