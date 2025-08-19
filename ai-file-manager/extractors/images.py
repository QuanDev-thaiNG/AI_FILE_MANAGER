from PIL import Image
import exifread
import os
import datetime
from pathlib import Path

class ImageExtractor:
    """Lớp trích xuất metadata từ file ảnh"""
    
    def __init__(self):
        pass
    
    def extract_metadata(self, file_path):
        """Trích xuất metadata từ file ảnh"""
        metadata = {}
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        # Trích xuất thông tin cơ bản bằng Pillow
        try:
            with Image.open(file_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                
                # Trích xuất thông tin EXIF nếu có
                exif = img._getexif()
                if exif:
                    # Một số tag EXIF phổ biến
                    exif_tags = {
                        0x010F: 'camera_make',      # Nhà sản xuất
                        0x0110: 'camera_model',     # Model
                        0x0132: 'datetime',         # Thời gian chụp
                        0x8825: 'gps_info',         # Thông tin GPS
                        0x9003: 'datetime_original', # Thời gian gốc
                        0x9004: 'datetime_digitized' # Thời gian số hóa
                    }
                    
                    for tag, value in exif.items():
                        if tag in exif_tags:
                            tag_name = exif_tags[tag]
                            metadata[tag_name] = value
        except Exception as e:
            print(f"Lỗi khi trích xuất metadata bằng Pillow: {e}")
        
        # Trích xuất thông tin EXIF chi tiết hơn bằng exifread
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                
                # Trích xuất thông tin GPS
                if 'GPS GPSLatitude' in tags and 'GPS GPSLatitudeRef' in tags:
                    lat = self._convert_to_degrees(tags['GPS GPSLatitude'].values)
                    lat_ref = tags['GPS GPSLatitudeRef'].values
                    if lat_ref == 'S':
                        lat = -lat
                    metadata['gps_lat'] = lat
                
                if 'GPS GPSLongitude' in tags and 'GPS GPSLongitudeRef' in tags:
                    lon = self._convert_to_degrees(tags['GPS GPSLongitude'].values)
                    lon_ref = tags['GPS GPSLongitudeRef'].values
                    if lon_ref == 'W':
                        lon = -lon
                    metadata['gps_lon'] = lon
                
                # Trích xuất thông tin thời gian
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    try:
                        metadata['datetime'] = datetime.datetime.strptime(
                            date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        pass
        except Exception as e:
            print(f"Lỗi khi trích xuất EXIF bằng exifread: {e}")
        
        return metadata
    
    def _convert_to_degrees(self, value):
        """Chuyển đổi giá trị GPS từ dạng phân số sang độ thập phân"""
        d = float(value[0].num) / float(value[0].den)
        m = float(value[1].num) / float(value[1].den)
        s = float(value[2].num) / float(value[2].den)
        return d + (m / 60.0) + (s / 3600.0)
    
    def extract_text_from_image(self, file_path):
        """Trích xuất text từ ảnh sử dụng OCR (cần cài đặt pytesseract)"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except ImportError:
            print("Cần cài đặt pytesseract để sử dụng OCR")
            return ""
        except Exception as e:
            print(f"Lỗi khi trích xuất text từ ảnh: {e}")
            return ""