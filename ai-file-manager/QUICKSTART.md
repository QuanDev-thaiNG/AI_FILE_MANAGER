# Hướng dẫn nhanh AI File Manager

## Cài đặt

1. Cài đặt Python 3.8 trở lên

2. Cài đặt các thư viện phụ thuộc:

```bash
pip install -r requirements.txt
```

3. Cài đặt các phần mềm bổ sung:
   - FFmpeg (cho xử lý video)
   - Tesseract OCR (cho OCR)

## Sử dụng cơ bản

### 1. Khởi tạo

Khởi tạo cơ sở dữ liệu và cấu hình:

```bash
python main.py init --db-path=./filemanager.db
```

### 2. Quét và đăng ký file

Quét thư mục và đăng ký file vào cơ sở dữ liệu:

```bash
python main.py ingest --directory="D:/Photos" --recursive
```

Sử dụng tùy chọn `--dry-run` để kiểm tra trước khi thực hiện:

```bash
python main.py ingest --directory="D:/Photos" --recursive --dry-run
```

### 3. Sắp xếp file theo quy tắc

Sắp xếp file theo quy tắc định nghĩa trong file YAML:

```bash
python main.py organize --rules-file="./rules/example_rules.yaml"
```

Sử dụng tùy chọn `--dry-run` để kiểm tra trước khi thực hiện:

```bash
python main.py organize --rules-file="./rules/example_rules.yaml" --dry-run
```

### 4. Tìm kiếm file

Tìm kiếm file theo tên:

```bash
python main.py search --filename="vacation"
```

Tìm kiếm file theo loại MIME:

```bash
python main.py search --mime-type="image/jpeg"
```

Tìm kiếm file theo thẻ:

```bash
python main.py search --tags="ảnh,2023"
```

Tìm kiếm file theo kích thước:

```bash
python main.py search --min-size=1000000 --max-size=5000000
```

Tìm kiếm file theo ngày tạo:

```bash
python main.py search --created-after="2023-01-01" --created-before="2023-12-31"
```

Tìm kiếm file trùng lặp:

```bash
python main.py search --duplicates
```

### 5. Quản lý thẻ

Thêm thẻ cho file:

```bash
python main.py tag add --file-path="D:/Photos/vacation.jpg" --tags="du lịch,biển"
```

Xóa thẻ khỏi file:

```bash
python main.py tag remove --file-path="D:/Photos/vacation.jpg" --tags="biển"
```

Liệt kê tất cả các thẻ:

```bash
python main.py tag list
```

Liệt kê thẻ của một file cụ thể:

```bash
python main.py tag list --file-path="D:/Photos/vacation.jpg"
```

### 6. Lập chỉ mục nội dung

Lập chỉ mục nội dung cho tất cả các file văn bản và PDF:

```bash
python main.py index
```

Lập chỉ mục nội dung cho một loại MIME cụ thể:

```bash
python main.py index --mime-type="application/pdf"
```

Xây dựng lại chỉ mục:

```bash
python main.py index --rebuild
```

## Ví dụ quy tắc sắp xếp

Xem file `rules/example_rules.yaml` để biết cách định nghĩa quy tắc sắp xếp file.

## Tìm hiểu thêm

Xem file `README.md` để biết thêm chi tiết về cấu trúc và tính năng của AI File Manager.