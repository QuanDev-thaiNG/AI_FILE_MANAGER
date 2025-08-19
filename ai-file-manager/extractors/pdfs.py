import pdfplumber
import os
from pathlib import Path
import re

class PDFExtractor:
    """Lớp trích xuất metadata và nội dung từ file PDF"""
    
    def __init__(self):
        pass
    
    def extract_metadata(self, file_path):
        """Trích xuất metadata từ file PDF"""
        metadata = {}
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # Số trang
                metadata['pages'] = len(pdf.pages)
                
                # Trích xuất metadata từ PDF
                if pdf.metadata:
                    # Tiêu đề
                    if 'Title' in pdf.metadata and pdf.metadata['Title']:
                        metadata['title'] = pdf.metadata['Title']
                    
                    # Tác giả
                    if 'Author' in pdf.metadata and pdf.metadata['Author']:
                        metadata['author'] = pdf.metadata['Author']
                    
                    # Từ khoá
                    if 'Keywords' in pdf.metadata and pdf.metadata['Keywords']:
                        metadata['keywords'] = pdf.metadata['Keywords']
                    
                    # Ngày tạo
                    if 'CreationDate' in pdf.metadata and pdf.metadata['CreationDate']:
                        metadata['creation_date'] = pdf.metadata['CreationDate']
                
                # Nếu không có tiêu đề trong metadata, thử trích xuất từ trang đầu
                if 'title' not in metadata or not metadata['title']:
                    first_page_text = pdf.pages[0].extract_text()
                    if first_page_text:
                        # Lấy dòng đầu tiên làm tiêu đề
                        lines = first_page_text.split('\n')
                        if lines:
                            metadata['title'] = lines[0].strip()
                
                # Kiểm tra xem PDF có phải là scan hay không
                metadata['has_ocr'] = False
                for i in range(min(3, len(pdf.pages))):
                    page = pdf.pages[i]
                    if not page.extract_text() and page.images:
                        metadata['has_ocr'] = True
                        break
        except Exception as e:
            print(f"Lỗi khi trích xuất metadata từ PDF: {e}")
        
        return metadata
    
    def extract_text(self, file_path, max_pages=None):
        """Trích xuất toàn bộ text từ file PDF"""
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_to_extract = pdf.pages[:max_pages] if max_pages else pdf.pages
                text = '\n\n'.join([page.extract_text() or '' for page in pages_to_extract])
                return text.strip()
        except Exception as e:
            print(f"Lỗi khi trích xuất text từ PDF: {e}")
            return ""
    
    def extract_tables(self, file_path, max_pages=None):
        """Trích xuất các bảng từ file PDF"""
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_to_extract = pdf.pages[:max_pages] if max_pages else pdf.pages
                
                for i, page in enumerate(pages_to_extract):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        tables.append({
                            'page': i + 1,
                            'data': table
                        })
                
                return tables
        except Exception as e:
            print(f"Lỗi khi trích xuất bảng từ PDF: {e}")
            return []
    
    def detect_language(self, text):
        """Phát hiện ngôn ngữ của văn bản"""
        try:
            from langdetect import detect
            
            if not text or len(text.strip()) < 10:
                return None
            
            return detect(text)
        except ImportError:
            print("Cần cài đặt langdetect để phát hiện ngôn ngữ")
            return None
        except Exception as e:
            print(f"Lỗi khi phát hiện ngôn ngữ: {e}")
            return None
    
    def extract_with_ocr(self, file_path, max_pages=3):
        """Trích xuất text từ PDF scan sử dụng OCR"""
        try:
            import pytesseract
            from PIL import Image
            import pdf2image
            
            # Chuyển PDF thành ảnh
            images = pdf2image.convert_from_path(file_path, dpi=300, first_page=1, last_page=max_pages)
            
            # Trích xuất text từ mỗi ảnh
            text = ''
            for i, img in enumerate(images):
                page_text = pytesseract.image_to_string(img)
                text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
            
            return text.strip()
        except ImportError:
            print("Cần cài đặt pytesseract và pdf2image để sử dụng OCR")
            return ""
        except Exception as e:
            print(f"Lỗi khi trích xuất text bằng OCR: {e}")
            return ""