# AI File Manager - Phiên bản Web

Đây là phiên bản web của AI File Manager, một công cụ quản lý file thông minh sử dụng AI để tổ chức và tìm kiếm các loại file khác nhau.

## Tính năng

- Giao diện web trực quan, dễ sử dụng
- Quét và đăng ký file vào cơ sở dữ liệu
- Trích xuất metadata từ nhiều loại file khác nhau
- Phát hiện file trùng lặp
- Tổ chức file theo quy tắc
- Tìm kiếm nâng cao với AI
- Gắn thẻ thông minh cho file

## Yêu cầu hệ thống

- Python 3.8 trở lên
- FFmpeg
- Tesseract OCR
- Các thư viện Python được liệt kê trong `requirements.txt`

## Cài đặt

1. Cài đặt các phụ thuộc:

```bash
pip install -r requirements.txt
```

2. Đảm bảo FFmpeg và Tesseract OCR đã được cài đặt trên hệ thống của bạn.

## Chạy ứng dụng web

```bash
python app.py
```

Ứng dụng sẽ chạy tại địa chỉ http://localhost:5000

## API Endpoints

- `/api/init` - Khởi tạo cơ sở dữ liệu
- `/api/ingest` - Quét và đăng ký file
- `/api/search` - Tìm kiếm file
- `/api/organize` - Tổ chức file theo quy tắc
- `/api/tags` - Lấy danh sách tất cả các thẻ
- `/api/tags/file` - Lấy thẻ của một file cụ thể
- `/api/tags/add` - Thêm thẻ cho file
- `/api/tags/remove` - Xóa thẻ khỏi file
- `/api/status` - Kiểm tra trạng thái hệ thống

## Triển khai

Ứng dụng có thể được triển khai lên các nền tảng như Heroku, AWS, hoặc bất kỳ máy chủ nào hỗ trợ Python và Flask.

```bash
gunicorn app:app
```

## Lưu ý

- Đảm bảo cấu hình đúng đường dẫn đến cơ sở dữ liệu và các thư mục dữ liệu.
- Khi triển khai lên môi trường sản xuất, hãy tắt chế độ debug và cấu hình bảo mật phù hợp.