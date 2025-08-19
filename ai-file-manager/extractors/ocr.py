import os
from pathlib import Path

class OCRExtractor:
    """Lớp trích xuất text từ ảnh và PDF scan sử dụng OCR"""
    
    def __init__(self, tesseract_cmd=None):
        """Khởi tạo với đường dẫn đến tesseract"""
        if tesseract_cmd:
            os.environ['TESSERACT_CMD'] = tesseract_cmd
    
    def extract_text_from_image(self, image_path, lang='vie+eng'):
        """Trích xuất text từ ảnh"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=lang)
            return text.strip()
        except ImportError:
            print("Cần cài đặt pytesseract để sử dụng OCR")
            return ""
        except Exception as e:
            print(f"Lỗi khi trích xuất text từ ảnh: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path, pages=None, lang='vie+eng'):
        """Trích xuất text từ PDF scan"""
        try:
            import pytesseract
            from PIL import Image
            import pdf2image
            
            # Chuyển PDF thành ảnh
            images = pdf2image.convert_from_path(
                pdf_path, 
                dpi=300, 
                first_page=pages[0] if pages else 1, 
                last_page=pages[-1] if pages else None
            )
            
            # Trích xuất text từ mỗi ảnh
            text = ''
            for i, img in enumerate(images):
                page_num = (pages[0] + i) if pages else (i + 1)
                page_text = pytesseract.image_to_string(img, lang=lang)
                text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
            
            return text.strip()
        except ImportError:
            print("Cần cài đặt pytesseract và pdf2image để sử dụng OCR")
            return ""
        except Exception as e:
            print(f"Lỗi khi trích xuất text từ PDF: {e}")
            return ""
    
    def preprocess_image(self, image_path, output_path=None):
        """Tiền xử lý ảnh để cải thiện kết quả OCR"""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            # Nếu không có đường dẫn đầu ra, tạo tên file mới
            if not output_path:
                path = Path(image_path)
                output_path = str(path.with_stem(f"{path.stem}_processed"))
            
            # Mở ảnh
            img = Image.open(image_path)
            
            # Chuyển sang grayscale
            img = img.convert('L')
            
            # Tăng độ tương phản
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Làm mờ nhẹ để giảm nhiễu
            img = img.filter(ImageFilter.GaussianBlur(0.5))
            
            # Làm sắc nét
            img = img.filter(ImageFilter.SHARPEN)
            
            # Lưu ảnh đã xử lý
            img.save(output_path)
            
            return output_path
        except ImportError:
            print("Cần cài đặt Pillow để xử lý ảnh")
            return image_path
        except Exception as e:
            print(f"Lỗi khi tiền xử lý ảnh: {e}")
            return image_path
    
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