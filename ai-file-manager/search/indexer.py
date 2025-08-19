import os
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class ContentIndexer:
    """Lớp đánh chỉ mục và tìm kiếm nội dung"""
    
    def __init__(self, db, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """Khởi tạo với kết nối database và mô hình embedding"""
        self.db = db
        self.model_name = model_name
        self.model = None
        self.index = None
        self.file_ids = []
        
        # Kiểm tra các thư viện cần thiết
        if not FAISS_AVAILABLE:
            print("Cảnh báo: Thư viện FAISS không khả dụng. Tìm kiếm vector sẽ bị vô hiệu hóa.")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Cảnh báo: Thư viện sentence-transformers không khả dụng. Tạo embedding sẽ bị vô hiệu hóa.")
        
        # Tải mô hình nếu có thể
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"Đã tải mô hình embedding: {model_name}")
            except Exception as e:
                print(f"Lỗi khi tải mô hình embedding: {e}")
    
    def index_text_content(self, file_id: int, content: str, chunk_size: int = 1000, overlap: int = 200) -> bool:
        """Đánh chỉ mục nội dung văn bản của file"""
        if not content or not file_id:
            return False
        
        # Chia nội dung thành các đoạn nhỏ
        chunks = self._chunk_text(content, chunk_size, overlap)
        
        # Lưu các đoạn vào database
        cursor = self.db.conn.cursor()
        try:
            # Xóa các đoạn cũ nếu có
            cursor.execute("DELETE FROM content_index WHERE file_id = ?", (file_id,))
            
            # Thêm các đoạn mới
            for i, chunk in enumerate(chunks):
                cursor.execute(
                    "INSERT INTO content_index (file_id, chunk_index, content) VALUES (?, ?, ?)",
                    (file_id, i, chunk))
            
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"Lỗi khi đánh chỉ mục nội dung: {e}")
            return False
    
    def create_embeddings(self, rebuild: bool = False) -> bool:
        """Tạo embedding cho tất cả các đoạn văn bản"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not self.model:
            print("Không thể tạo embedding: Mô hình không khả dụng")
            return False
        
        cursor = self.db.conn.cursor()
        
        try:
            # Lấy các đoạn chưa có embedding hoặc tất cả nếu rebuild
            if rebuild:
                cursor.execute("SELECT id, file_id, content FROM content_index")
            else:
                cursor.execute(
                    """SELECT ci.id, ci.file_id, ci.content 
                       FROM content_index ci 
                       LEFT JOIN embeddings e ON ci.id = e.content_id 
                       WHERE e.id IS NULL""")
            
            chunks = cursor.fetchall()
            
            if not chunks:
                print("Không có đoạn văn bản nào cần tạo embedding")
                return True
            
            print(f"Đang tạo embedding cho {len(chunks)} đoạn văn bản...")
            
            # Tạo embedding theo batch
            batch_size = 32
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                texts = [chunk['content'] for chunk in batch]
                embeddings = self.model.encode(texts)
                
                # Lưu embedding vào database
                for j, emb in enumerate(embeddings):
                    chunk_id = batch[j]['id']
                    file_id = batch[j]['file_id']
                    
                    # Chuyển đổi embedding thành bytes
                    emb_bytes = np.array(emb, dtype=np.float32).tobytes()
                    
                    # Kiểm tra xem embedding đã tồn tại chưa
                    cursor.execute(
                        "SELECT id FROM embeddings WHERE content_id = ?", 
                        (chunk_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute(
                            "UPDATE embeddings SET vector = ? WHERE id = ?",
                            (emb_bytes, existing['id']))
                    else:
                        cursor.execute(
                            "INSERT INTO embeddings (content_id, file_id, vector) VALUES (?, ?, ?)",
                            (chunk_id, file_id, emb_bytes))
                
                self.db.conn.commit()
                print(f"Đã tạo embedding cho {min(i+batch_size, len(chunks))}/{len(chunks)} đoạn văn bản")
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"Lỗi khi tạo embedding: {e}")
            return False
    
    def build_faiss_index(self) -> bool:
        """Xây dựng chỉ mục FAISS từ các embedding"""
        if not FAISS_AVAILABLE:
            print("Không thể xây dựng chỉ mục FAISS: Thư viện không khả dụng")
            return False
        
        if not self.model:
            print("Không thể xây dựng chỉ mục FAISS: Mô hình không khả dụng")
            return False
        
        cursor = self.db.conn.cursor()
        
        try:
            # Lấy tất cả các embedding
            cursor.execute(
                """SELECT e.id, e.file_id, e.content_id, e.vector, ci.content 
                   FROM embeddings e 
                   JOIN content_index ci ON e.content_id = ci.id""")
            
            embeddings = cursor.fetchall()
            
            if not embeddings:
                print("Không có embedding nào để xây dựng chỉ mục FAISS")
                return False
            
            print(f"Đang xây dựng chỉ mục FAISS cho {len(embeddings)} embedding...")
            
            # Lấy kích thước embedding
            vector_size = len(np.frombuffer(embeddings[0]['vector'], dtype=np.float32))
            
            # Tạo chỉ mục FAISS
            self.index = faiss.IndexFlatL2(vector_size)
            
            # Thêm các embedding vào chỉ mục
            vectors = np.zeros((len(embeddings), vector_size), dtype=np.float32)
            self.file_ids = []
            
            for i, emb in enumerate(embeddings):
                vector = np.frombuffer(emb['vector'], dtype=np.float32)
                vectors[i] = vector
                self.file_ids.append((emb['file_id'], emb['content_id']))
            
            self.index.add(vectors)
            print(f"Đã xây dựng chỉ mục FAISS cho {len(embeddings)} embedding")
            
            return True
        except Exception as e:
            print(f"Lỗi khi xây dựng chỉ mục FAISS: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm nội dung dựa trên truy vấn"""
        if not query:
            return []
        
        # Tìm kiếm theo từ khóa nếu không có FAISS hoặc mô hình
        if not FAISS_AVAILABLE or not self.model or not self.index:
            return self._keyword_search(query, top_k)
        
        try:
            # Tạo embedding cho truy vấn
            query_vector = self.model.encode([query])[0].reshape(1, -1).astype(np.float32)
            
            # Tìm kiếm các embedding gần nhất
            distances, indices = self.index.search(query_vector, top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.file_ids):
                    continue
                
                file_id, content_id = self.file_ids[idx]
                distance = distances[0][i]
                
                # Lấy thông tin file và nội dung
                file_info = self._get_file_info(file_id)
                content = self._get_content(content_id)
                
                if file_info and content:
                    results.append({
                        'file_id': file_id,
                        'file_path': file_info['abs_path'],
                        'filename': file_info['filename'],
                        'content': content,
                        'score': float(1.0 / (1.0 + distance))  # Chuyển đổi khoảng cách thành điểm số
                    })
            
            return results
        except Exception as e:
            print(f"Lỗi khi tìm kiếm vector: {e}")
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm nội dung dựa trên từ khóa"""
        cursor = self.db.conn.cursor()
        
        # Chuẩn bị truy vấn SQL
        search_terms = query.split()
        like_clauses = []
        params = []
        
        for term in search_terms:
            like_clauses.append("ci.content LIKE ?")
            params.append(f"%{term}%")
        
        where_clause = " AND ".join(like_clauses)
        
        try:
            # Thực hiện tìm kiếm
            cursor.execute(
                f"""SELECT ci.id, ci.file_id, ci.content, f.abs_path, f.filename 
                    FROM content_index ci 
                    JOIN files f ON ci.file_id = f.id 
                    WHERE {where_clause} 
                    LIMIT ?""",
                params + [top_k])
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'file_id': row['file_id'],
                    'file_path': row['abs_path'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'score': 1.0  # Điểm số mặc định cho tìm kiếm từ khóa
                })
            
            return results
        except Exception as e:
            print(f"Lỗi khi tìm kiếm từ khóa: {e}")
            return []
    
    def _get_file_info(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin file từ database"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT id, abs_path, filename, size, created_at, modified_at, hash FROM files WHERE id = ?",
            (file_id,))
        
        file_info = cursor.fetchone()
        return dict(file_info) if file_info else None
    
    def _get_content(self, content_id: int) -> Optional[str]:
        """Lấy nội dung từ database"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT content FROM content_index WHERE id = ?", (content_id,))
        
        content = cursor.fetchone()
        return content['content'] if content else None
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chia văn bản thành các đoạn nhỏ với độ chồng lấp"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Điều chỉnh vị trí kết thúc để tránh cắt giữa từ
            if end < text_len:
                # Tìm khoảng trắng gần nhất
                while end > start and text[end] not in [' ', '\n', '.', ',', '!', '?']:
                    end -= 1
                
                # Nếu không tìm thấy khoảng trắng, sử dụng vị trí ban đầu
                if end == start:
                    end = min(start + chunk_size, text_len)
            
            chunks.append(text[start:end])
            start = end - overlap  # Chồng lấp với đoạn trước
            
            # Đảm bảo vị trí bắt đầu hợp lệ
            if start < 0:
                start = 0
        
        return chunks