# Hướng dẫn kiểm thử AI File Manager

## Cài đặt môi trường kiểm thử

1. Cài đặt các thư viện phụ thuộc cho kiểm thử:

```bash
pip install pytest pytest-cov mock
```

2. Đảm bảo bạn đã cài đặt các phần mềm bổ sung cần thiết:
   - FFmpeg (cho kiểm thử xử lý video)
   - Tesseract OCR (cho kiểm thử OCR)

## Chạy kiểm thử

### Chạy tất cả các kiểm thử

```bash
python -m pytest tests/
```

### Chạy kiểm thử cho một module cụ thể

```bash
python -m pytest tests/test_core.py
```

### Chạy kiểm thử với báo cáo độ phủ

```bash
python -m pytest --cov=. tests/
```

### Chạy kiểm thử với báo cáo chi tiết

```bash
python -m pytest -v tests/
```

## Cấu trúc kiểm thử

Dự án sử dụng `unittest` làm framework kiểm thử chính. Các file kiểm thử được tổ chức theo cấu trúc sau:

- `tests/test_core.py`: Kiểm thử cho các module cơ bản (db, ingest, mimetype, hashing)
- `tests/test_extractors.py`: Kiểm thử cho các module trích xuất metadata (images, pdfs, videos, ocr)
- `tests/test_rules.py`: Kiểm thử cho engine quy tắc và schema
- `tests/test_actions.py`: Kiểm thử cho các hành động file (move, copy, tag)
- `tests/test_search.py`: Kiểm thử cho tìm kiếm và lập chỉ mục
- `tests/test_cli.py`: Kiểm thử cho giao diện dòng lệnh

## Viết kiểm thử mới

Khi viết kiểm thử mới, vui lòng tuân thủ các nguyên tắc sau:

1. Mỗi kiểm thử nên tập trung vào một chức năng cụ thể
2. Sử dụng `setUp` và `tearDown` để chuẩn bị và dọn dẹp môi trường kiểm thử
3. Sử dụng `mock` để giả lập các phụ thuộc bên ngoài
4. Đặt tên kiểm thử rõ ràng, mô tả chức năng đang kiểm thử
5. Thêm docstring cho mỗi kiểm thử để mô tả mục đích

Ví dụ về một kiểm thử tốt:

```python
def test_calculate_hash(self):
    """Kiểm tra tính toán hash SHA-256"""
    # Tạo file tạm thời cho kiểm thử
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(b"Test content")
        temp_file.flush()
        
        # Tính hash của file
        file_hash = self.hasher.calculate_hash(temp_file.name)
        
        # Kiểm tra kết quả
        self.assertIsNotNone(file_hash)
        self.assertEqual(len(file_hash), 64)  # SHA-256 hash có độ dài 64 ký tự hex
```

## Kiểm thử tích hợp

Ngoài kiểm thử đơn vị, bạn cũng nên chạy kiểm thử tích hợp để đảm bảo các module hoạt động tốt với nhau:

1. Tạo một thư mục tạm thời với các file mẫu
2. Chạy quy trình đầy đủ: ingest -> organize -> search
3. Kiểm tra kết quả cuối cùng

## Xử lý lỗi kiểm thử

Nếu kiểm thử thất bại, hãy kiểm tra:

1. Môi trường kiểm thử có đầy đủ các phụ thuộc không
2. Các mock có được cấu hình đúng không
3. Dữ liệu kiểm thử có hợp lệ không
4. Có thay đổi gần đây nào ảnh hưởng đến chức năng không

## Kiểm thử hiệu suất

Để kiểm thử hiệu suất, bạn có thể sử dụng:

```bash
python -m pytest tests/test_performance.py --benchmark-save=baseline
```

Lưu ý: Hiện tại chưa có file `test_performance.py`, bạn có thể tạo file này để kiểm thử hiệu suất của các chức năng quan trọng.