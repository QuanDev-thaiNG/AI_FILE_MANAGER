import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

class Searcher:
    def __init__(self, db):
        self.db = db
        self.model = None
        try:
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        except Exception as e:
            print(f"Lỗi khi tải mô hình tìm kiếm: {e}")
    
    def search(self, query, limit=10):
        """
        Phương thức tìm kiếm chung, sử dụng tìm kiếm ngữ nghĩa nếu có thể,
        nếu không sẽ sử dụng tìm kiếm văn bản cơ bản
        """
        try:
            # Ưu tiên sử dụng tìm kiếm ngữ nghĩa nếu mô hình đã được tải
            if self.model:
                return self.search_by_semantic(query, limit)
            else:
                return self.search_by_text(query, limit)
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            # Fallback về tìm kiếm văn bản cơ bản
            return self.search_by_text(query, limit)
    
    def search_by_text(self, query, limit=10):
        """
        Tìm kiếm tập tin dựa trên nội dung văn bản
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # Tìm kiếm cơ bản dựa trên từ khóa trong extracted_text
            results = self.db.fetch_query(
                "SELECT id, path, filename, extension, size, mime_type FROM files "
                "WHERE extracted_text LIKE ? LIMIT ?",
                (f"%{query}%", limit)
            )
            
            return [{
                'id': row[0],
                'path': row[1],
                'filename': row[2],
                'extension': row[3],
                'size': row[4],
                'mime_type': row[5]
            } for row in results]
        except Exception as e:
            print(f"Lỗi khi tìm kiếm văn bản: {e}")
            return []
    
    def search_by_semantic(self, query, limit=10):
        """
        Tìm kiếm tập tin dựa trên ngữ nghĩa sử dụng embedding
        """
        try:
            if not self.model:
                return self.search_by_text(query, limit)
            
            if not self.db.conn:
                self.db.connect()
            
            # Lấy tất cả các file có embedding
            files = self.db.fetch_query(
                "SELECT id, path, filename, extension, size, mime_type, embedding_path FROM files "
                "WHERE embedding_path IS NOT NULL"
            )
            
            if not files:
                return self.search_by_text(query, limit)
            
            # Tạo embedding cho query
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            
            # Tính toán độ tương đồng với các file
            similarities = []
            for file in files:
                file_id, path, filename, extension, size, mime_type, embedding_path = file
                
                if os.path.exists(embedding_path):
                    try:
                        file_embedding = np.load(embedding_path)
                        similarity = util.pytorch_cos_sim(query_embedding, file_embedding).item()
                        similarities.append((similarity, {
                            'id': file_id,
                            'path': path,
                            'filename': filename,
                            'extension': extension,
                            'size': size,
                            'mime_type': mime_type
                        }))
                    except Exception as e:
                        print(f"Lỗi khi tính toán độ tương đồng cho file {path}: {e}")
            
            # Sắp xếp kết quả theo độ tương đồng giảm dần
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Trả về limit kết quả đầu tiên
            return [item[1] for item in similarities[:limit]]
        except Exception as e:
            print(f"Lỗi khi tìm kiếm ngữ nghĩa: {e}")
            return self.search_by_text(query, limit)
    
    def search_by_metadata(self, criteria, limit=10):
        """
        Tìm kiếm tập tin dựa trên metadata
        criteria: dict chứa các tiêu chí tìm kiếm
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            query_parts = []
            params = []
            
            # Xây dựng truy vấn dựa trên các tiêu chí
            for key, value in criteria.items():
                if key == 'extension':
                    query_parts.append("extension = ?")
                    params.append(value)
                elif key == 'mime_type':
                    query_parts.append("mime_type LIKE ?")
                    params.append(f"%{value}%")
                elif key == 'size_min':
                    query_parts.append("size >= ?")
                    params.append(int(value))
                elif key == 'size_max':
                    query_parts.append("size <= ?")
                    params.append(int(value))
                elif key == 'created_after':
                    query_parts.append("created_date >= ?")
                    params.append(value)
                elif key == 'created_before':
                    query_parts.append("created_date <= ?")
                    params.append(value)
                elif key == 'modified_after':
                    query_parts.append("modified_date >= ?")
                    params.append(value)
                elif key == 'modified_before':
                    query_parts.append("modified_date <= ?")
                    params.append(value)
                elif key == 'filename':
                    query_parts.append("filename LIKE ?")
                    params.append(f"%{value}%")
            
            if not query_parts:
                return []
            
            # Tạo truy vấn SQL
            query = "SELECT id, path, filename, extension, size, mime_type FROM files WHERE " + " AND ".join(query_parts) + " LIMIT ?"
            params.append(limit)
            
            # Thực thi truy vấn
            results = self.db.fetch_query(query, tuple(params))
            
            return [{
                'id': row[0],
                'path': row[1],
                'filename': row[2],
                'extension': row[3],
                'size': row[4],
                'mime_type': row[5]
            } for row in results]
        except Exception as e:
            print(f"Lỗi khi tìm kiếm theo metadata: {e}")
            return []