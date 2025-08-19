import hashlib
import imagehash
from PIL import Image
from pathlib import Path

class FileHasher:
    """Lớp tính toán và so sánh hash của file"""
    
    @staticmethod
    def hash_sha256(file_path):
        """Tính toán hash SHA-256 của file"""
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1<<20), b''):
                h.update(chunk)
        return h.hexdigest()
    
    @staticmethod
    def hash_sha256_short(file_path, length=8):
        """Tính toán hash SHA-256 ngắn của file (8 ký tự đầu)"""
        full_hash = FileHasher.hash_sha256(file_path)
        return full_hash[:length]
    
    @staticmethod
    def perceptual_hash(image_path):
        """Tính toán perceptual hash cho ảnh để phát hiện gần-trùng"""
        try:
            img = Image.open(image_path)
            # Sử dụng phương pháp phổ biến: phHash
            hash_value = imagehash.phash(img)
            return str(hash_value)
        except Exception as e:
            print(f"Lỗi khi tính perceptual hash cho {image_path}: {e}")
            return None
    
    @staticmethod
    def compare_perceptual_hash(hash1, hash2, threshold=10):
        """So sánh hai perceptual hash, trả về True nếu gần giống nhau"""
        if not hash1 or not hash2:
            return False
        
        try:
            h1 = imagehash.hex_to_hash(hash1) if isinstance(hash1, str) else hash1
            h2 = imagehash.hex_to_hash(hash2) if isinstance(hash2, str) else hash2
            difference = h1 - h2
            return difference < threshold
        except Exception as e:
            print(f"Lỗi khi so sánh perceptual hash: {e}")
            return False

class DuplicateFinder:
    """Lớp phát hiện file trùng lặp hoặc gần-trùng"""
    
    def __init__(self, db_connection=None):
        self.db_conn = db_connection
        self.hash_map = {}  # {hash: file_path}
        self.perceptual_hash_map = {}  # {phash: file_path}
    
    def find_exact_duplicates(self, directory):
        """Tìm các file trùng lặp chính xác trong thư mục"""
        duplicates = {}  # {hash: [file_paths]}
        dir_path = Path(directory)
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                try:
                    file_hash = FileHasher.hash_sha256(file_path)
                    
                    if file_hash in duplicates:
                        duplicates[file_hash].append(str(file_path))
                    else:
                        duplicates[file_hash] = [str(file_path)]
                except Exception as e:
                    print(f"Lỗi khi xử lý {file_path}: {e}")
        
        # Lọc ra các hash có nhiều hơn 1 file
        return {h: files for h, files in duplicates.items() if len(files) > 1}
    
    def find_near_duplicates_images(self, directory, threshold=10):
        """Tìm các ảnh gần-trùng trong thư mục"""
        from core.mimetype import MimeTypeDetector
        
        mime_detector = MimeTypeDetector()
        near_duplicates = {}  # {file_path: [similar_files]}
        dir_path = Path(directory)
        
        # Thu thập tất cả ảnh và tính perceptual hash
        image_hashes = {}
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                try:
                    mime_type = mime_detector.detect_from_file(file_path)
                    if mime_type and mime_type.startswith('image/'):
                        phash = FileHasher.perceptual_hash(file_path)
                        if phash:
                            image_hashes[str(file_path)] = phash
                except Exception as e:
                    print(f"Lỗi khi xử lý {file_path}: {e}")
        
        # So sánh từng cặp ảnh
        processed = set()
        
        for file1, hash1 in image_hashes.items():
            if file1 in processed:
                continue
                
            similar_files = []
            
            for file2, hash2 in image_hashes.items():
                if file1 != file2 and file2 not in processed:
                    if FileHasher.compare_perceptual_hash(hash1, hash2, threshold):
                        similar_files.append(file2)
            
            if similar_files:
                near_duplicates[file1] = similar_files
                processed.add(file1)
                processed.update(similar_files)
        
        return near_duplicates