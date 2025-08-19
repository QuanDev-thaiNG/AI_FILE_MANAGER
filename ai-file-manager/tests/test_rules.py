import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Thêm thư mục gốc vào sys.path để import các module
sys.path.insert(0, str(Path(__file__).parent.parent))

from rules.engine import RulesEngine
from rules.schemas import validate_rules_file, get_rule_template

class TestRulesEngine(unittest.TestCase):
    """Kiểm thử cho module RulesEngine"""
    
    def setUp(self):
        self.rules_yaml = """
        rules:
          - name: "Sắp xếp ảnh"
            description: "Di chuyển ảnh vào thư mục theo năm và tháng"
            if:
              mimetype: "image/*"
              exif:
                has_date: true
            then:
              move: "Photos/{exif.year}/{exif.month}/{filename}"
              tags: ["ảnh", "{exif.year}"]
          
          - name: "Sắp xếp PDF"
            description: "Di chuyển PDF vào thư mục tài liệu"
            if:
              extension: ".pdf"
            then:
              move: "Documents/{language}/{filename}"
              tags: ["tài liệu"]
        """
        
        # Tạo mock cho việc đọc file YAML
        self.mock_open = mock_open(read_data=self.rules_yaml)
        
        # Tạo đối tượng RulesEngine với mock
        with patch('builtins.open', self.mock_open):
            self.engine = RulesEngine('rules.yaml')
    
    def test_load_rules(self):
        """Kiểm tra tải quy tắc từ file YAML"""
        # Kiểm tra số lượng quy tắc đã tải
        self.assertEqual(len(self.engine.rules), 2)
        
        # Kiểm tra nội dung quy tắc đầu tiên
        rule1 = self.engine.rules[0]
        self.assertEqual(rule1['name'], "Sắp xếp ảnh")
        self.assertEqual(rule1['description'], "Di chuyển ảnh vào thư mục theo năm và tháng")
        self.assertEqual(rule1['if']['mimetype'], "image/*")
        self.assertTrue(rule1['if']['exif']['has_date'])
        self.assertEqual(rule1['then']['move'], "Photos/{exif.year}/{exif.month}/{filename}")
        self.assertEqual(rule1['then']['tags'], ["ảnh", "{exif.year}"])
        
        # Kiểm tra nội dung quy tắc thứ hai
        rule2 = self.engine.rules[1]
        self.assertEqual(rule2['name'], "Sắp xếp PDF")
        self.assertEqual(rule2['if']['extension'], ".pdf")
        self.assertEqual(rule2['then']['move'], "Documents/{language}/{filename}")
    
    def test_evaluate_condition_mimetype(self):
        """Kiểm tra đánh giá điều kiện MIME type"""
        # Tạo thông tin file mẫu
        file_info = {
            'mime_type': 'image/jpeg',
            'filename': 'test.jpg',
            'extension': '.jpg',
            'size': 1024,
            'created_at': '2023-01-01 00:00:00',
            'metadata': {
                'exif': {
                    'has_date': True,
                    'year': '2023',
                    'month': '01'
                }
            }
        }
        
        # Kiểm tra điều kiện MIME type khớp
        condition = {'mimetype': 'image/*'}
        self.assertTrue(self.engine.evaluate_condition(condition, file_info))
        
        # Kiểm tra điều kiện MIME type không khớp
        condition = {'mimetype': 'video/*'}
        self.assertFalse(self.engine.evaluate_condition(condition, file_info))
    
    def test_evaluate_condition_extension(self):
        """Kiểm tra đánh giá điều kiện phần mở rộng"""
        # Tạo thông tin file mẫu
        file_info = {
            'mime_type': 'application/pdf',
            'filename': 'test.pdf',
            'extension': '.pdf',
            'size': 1024,
            'created_at': '2023-01-01 00:00:00'
        }
        
        # Kiểm tra điều kiện phần mở rộng khớp
        condition = {'extension': '.pdf'}
        self.assertTrue(self.engine.evaluate_condition(condition, file_info))
        
        # Kiểm tra điều kiện phần mở rộng không khớp
        condition = {'extension': '.docx'}
        self.assertFalse(self.engine.evaluate_condition(condition, file_info))
    
    def test_format_path(self):
        """Kiểm tra định dạng đường dẫn dựa trên mẫu"""
        # Tạo thông tin file mẫu
        file_info = {
            'filename': 'test.jpg',
            'metadata': {
                'exif': {
                    'year': '2023',
                    'month': '01'
                }
            }
        }
        
        # Kiểm tra định dạng đường dẫn
        template = "Photos/{exif.year}/{exif.month}/{filename}"
        expected_path = "Photos/2023/01/test.jpg"
        self.assertEqual(self.engine.format_path(template, file_info), expected_path)
    
    def test_apply_rules(self):
        """Kiểm tra áp dụng quy tắc cho file"""
        # Tạo thông tin file ảnh
        image_info = {
            'mime_type': 'image/jpeg',
            'filename': 'test.jpg',
            'extension': '.jpg',
            'size': 1024,
            'created_at': '2023-01-01 00:00:00',
            'metadata': {
                'exif': {
                    'has_date': True,
                    'year': '2023',
                    'month': '01'
                }
            }
        }
        
        # Áp dụng quy tắc cho file ảnh
        action_plan = self.engine.apply_rules(image_info)
        
        # Kiểm tra kết quả
        self.assertEqual(action_plan['action'], 'move')
        self.assertEqual(action_plan['target_path'], 'Photos/2023/01/test.jpg')
        self.assertEqual(action_plan['tags'], ["ảnh", "2023"])
        
        # Tạo thông tin file PDF
        pdf_info = {
            'mime_type': 'application/pdf',
            'filename': 'test.pdf',
            'extension': '.pdf',
            'size': 1024,
            'created_at': '2023-01-01 00:00:00',
            'metadata': {
                'language': 'vi'
            }
        }
        
        # Áp dụng quy tắc cho file PDF
        action_plan = self.engine.apply_rules(pdf_info)
        
        # Kiểm tra kết quả
        self.assertEqual(action_plan['action'], 'move')
        self.assertEqual(action_plan['target_path'], 'Documents/vi/test.pdf')
        self.assertEqual(action_plan['tags'], ["tài liệu"])

class TestRulesSchemas(unittest.TestCase):
    """Kiểm thử cho module schemas"""
    
    def test_validate_rules_file(self):
        """Kiểm tra xác thực file quy tắc"""
        # Tạo dữ liệu quy tắc hợp lệ
        valid_rules = {
            'rules': [
                {
                    'name': 'Test Rule',
                    'description': 'Test Description',
                    'if': {
                        'mimetype': 'image/*'
                    },
                    'then': {
                        'move': 'test/{filename}',
                        'tags': ['test']
                    }
                }
            ]
        }
        
        # Kiểm tra xác thực quy tắc hợp lệ
        result = validate_rules_file(valid_rules)
        self.assertTrue(result['valid'])
        self.assertIsNone(result['errors'])
        
        # Tạo dữ liệu quy tắc không hợp lệ (thiếu trường 'then')
        invalid_rules = {
            'rules': [
                {
                    'name': 'Test Rule',
                    'description': 'Test Description',
                    'if': {
                        'mimetype': 'image/*'
                    }
                    # Thiếu trường 'then'
                }
            ]
        }
        
        # Kiểm tra xác thực quy tắc không hợp lệ
        result = validate_rules_file(invalid_rules)
        self.assertFalse(result['valid'])
        self.assertIsNotNone(result['errors'])
    
    def test_get_rule_template(self):
        """Kiểm tra lấy mẫu quy tắc"""
        # Lấy mẫu quy tắc
        template = get_rule_template()
        
        # Kiểm tra xem mẫu có chứa các trường cần thiết không
        self.assertIn('rules', template)
        self.assertTrue(isinstance(template['rules'], list))
        self.assertGreater(len(template['rules']), 0)
        
        # Kiểm tra cấu trúc của quy tắc đầu tiên
        rule = template['rules'][0]
        self.assertIn('name', rule)
        self.assertIn('description', rule)
        self.assertIn('if', rule)
        self.assertIn('then', rule)

if __name__ == '__main__':
    unittest.main()