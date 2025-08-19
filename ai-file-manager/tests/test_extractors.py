import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.images import ImageExtractor
from extractors.pdfs import PDFExtractor
from extractors.videos import VideoExtractor
from extractors.ocr import OCRExtractor

class TestImageExtractor(unittest.TestCase):
    """Kiểm thử cho module ImageExtractor"""
    
    def setUp(self):
        self.extractor = ImageExtractor()
        
    @patch('PIL.Image.open')
    def test_extract_metadata(self, mock_image_open):
        """Kiểm tra trích xuất metadata từ ảnh"""
        # Tạo mock cho đối tượng Image
        mock_img = MagicMock()
        mock_img.format = 'JPEG'
        mock_img.size = (1920, 1080)
        mock_img.info = {'jfif': 72}
        mock_image_open.return_value = mock_img
        
        # Gọi hàm trích xuất metadata
        metadata = self.extractor.extract_metadata('test.jpg')
        
        # Kiểm tra kết quả
        self.assertEqual(metadata['format'], 'JPEG')
        self.assertEqual(metadata['width'], 1920)
        self.assertEqual(metadata['height'], 1080)
        self.assertEqual(metadata['resolution'], 72)
    
    @patch('exifread.process_file')
    def test_extract_exif(self, mock_process_file):
        """Kiểm tra trích xuất thông tin EXIF"""
        # Tạo mock cho kết quả exifread
        mock_tags = {
            'EXIF DateTimeOriginal': MagicMock(values='2023:01:01 12:00:00'),
            'GPS GPSLatitude': MagicMock(values=[21, 1, 0]),
            'GPS GPSLatitudeRef': MagicMock(values='N'),
            'GPS GPSLongitude': MagicMock(values=[105, 51, 0]),
            'GPS GPSLongitudeRef': MagicMock(values='E'),
            'Image Make': MagicMock(values='Test Camera'),
            'Image Model': MagicMock(values='Test Model')
        }
        mock_process_file.return_value = mock_tags
        
        # Mở file giả
        with tempfile.NamedTemporaryFile() as temp_file:
            # Gọi hàm trích xuất EXIF
            exif_data = self.extractor.extract_exif(temp_file.name)
            
            # Kiểm tra kết quả
            self.assertEqual(exif_data['date_time'], '2023-01-01 12:00:00')
            self.assertEqual(exif_data['camera_make'], 'Test Camera')
            self.assertEqual(exif_data['camera_model'], 'Test Model')
            self.assertAlmostEqual(exif_data['latitude'], 21.0)
            self.assertAlmostEqual(exif_data['longitude'], 105.85)

class TestPDFExtractor(unittest.TestCase):
    """Kiểm thử cho module PDFExtractor"""
    
    def setUp(self):
        self.extractor = PDFExtractor()
    
    @patch('pdfplumber.open')
    def test_extract_metadata(self, mock_pdf_open):
        """Kiểm tra trích xuất metadata từ PDF"""
        # Tạo mock cho đối tượng PDF
        mock_pdf = MagicMock()
        mock_pdf.metadata = {
            'Title': 'Test Document',
            'Author': 'Test Author',
            'Creator': 'Test Creator',
            'Producer': 'Test Producer',
            'CreationDate': "D:20230101120000",
            'Keywords': 'test, pdf, document'
        }
        mock_pdf.pages = [MagicMock(), MagicMock(), MagicMock()]
        mock_pdf_open.return_value = mock_pdf
        mock_pdf.__enter__.return_value = mock_pdf
        
        # Gọi hàm trích xuất metadata
        metadata = self.extractor.extract_metadata('test.pdf')
        
        # Kiểm tra kết quả
        self.assertEqual(metadata['title'], 'Test Document')
        self.assertEqual(metadata['author'], 'Test Author')
        self.assertEqual(metadata['creator'], 'Test Creator')
        self.assertEqual(metadata['producer'], 'Test Producer')
        self.assertEqual(metadata['creation_date'], '2023-01-01 12:00:00')
        self.assertEqual(metadata['keywords'], 'test, pdf, document')
        self.assertEqual(metadata['pages'], 3)
    
    @patch('pdfplumber.open')
    def test_extract_text(self, mock_pdf_open):
        """Kiểm tra trích xuất văn bản từ PDF"""
        # Tạo mock cho đối tượng PDF và trang
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf_open.return_value = mock_pdf
        mock_pdf.__enter__.return_value = mock_pdf
        
        # Gọi hàm trích xuất văn bản
        text = self.extractor.extract_text('test.pdf')
        
        # Kiểm tra kết quả
        self.assertEqual(text, "Page 1 content\nPage 2 content")

class TestVideoExtractor(unittest.TestCase):
    """Kiểm thử cho module VideoExtractor"""
    
    def setUp(self):
        self.extractor = VideoExtractor()
    
    @patch('subprocess.run')
    def test_extract_metadata(self, mock_run):
        """Kiểm tra trích xuất metadata từ video"""
        # Tạo mock cho kết quả ffprobe
        mock_result = MagicMock()
        mock_result.stdout = '''
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "codec_name": "h264"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2
                }
            ],
            "format": {
                "filename": "test.mp4",
                "nb_streams": 2,
                "format_name": "mp4",
                "duration": "120.000000",
                "size": "10485760",
                "bit_rate": "699050",
                "tags": {
                    "title": "Test Video",
                    "encoder": "Test Encoder"
                }
            }
        }
        '''
        mock_run.return_value = mock_result
        
        # Gọi hàm trích xuất metadata
        metadata = self.extractor.extract_metadata('test.mp4')
        
        # Kiểm tra kết quả
        self.assertEqual(metadata['format'], 'mp4')
        self.assertEqual(metadata['duration'], 120.0)
        self.assertEqual(metadata['size'], 10485760)
        self.assertEqual(metadata['bitrate'], 699050)
        self.assertEqual(metadata['title'], 'Test Video')
        self.assertEqual(metadata['video_codec'], 'h264')
        self.assertEqual(metadata['width'], 1920)
        self.assertEqual(metadata['height'], 1080)
        self.assertEqual(metadata['fps'], 30.0)
        self.assertEqual(metadata['audio_codec'], 'aac')
        self.assertEqual(metadata['sample_rate'], 48000)
        self.assertEqual(metadata['channels'], 2)

class TestOCRExtractor(unittest.TestCase):
    """Kiểm thử cho module OCRExtractor"""
    
    def setUp(self):
        self.extractor = OCRExtractor()
    
    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    def test_extract_text_from_image(self, mock_image_open, mock_image_to_string):
        """Kiểm tra trích xuất văn bản từ ảnh"""
        # Tạo mock cho đối tượng Image và kết quả OCR
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        mock_image_to_string.return_value = "This is a test OCR result."
        
        # Gọi hàm trích xuất văn bản
        text = self.extractor.extract_text_from_image('test.jpg')
        
        # Kiểm tra kết quả
        self.assertEqual(text, "This is a test OCR result.")
    
    @patch('langdetect.detect')
    def test_detect_language(self, mock_detect):
        """Kiểm tra phát hiện ngôn ngữ"""
        # Tạo mock cho kết quả langdetect
        mock_detect.return_value = 'vi'
        
        # Gọi hàm phát hiện ngôn ngữ
        lang = self.extractor.detect_language("Đây là văn bản tiếng Việt.")
        
        # Kiểm tra kết quả
        self.assertEqual(lang, 'vi')

if __name__ == '__main__':
    unittest.main()