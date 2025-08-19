# AI File Manager

Công cụ quản lý và sắp xếp tập tin thông minh sử dụng AI để phân loại, tổ chức và tìm kiếm các tập tin như ảnh, văn bản, video và PDF.

## Tính năng chính

- **Quét và đăng ký file**: Tự động quét và thu thập metadata từ các tập tin
- **Trích xuất metadata**: Hỗ trợ trích xuất thông tin từ ảnh (EXIF), PDF, video
- **Phát hiện trùng lặp**: Tìm và quản lý các tập tin trùng lặp
- **Quy tắc tổ chức**: Hệ thống quy tắc linh hoạt dựa trên YAML để tự động sắp xếp tập tin
- **Tìm kiếm nâng cao**: Tìm kiếm theo metadata, nội dung, và tìm kiếm ngữ nghĩa dựa trên vector
- **Gắn thẻ thông minh**: Hệ thống gắn thẻ để phân loại và tìm kiếm dễ dàng

## Cài đặt

### Yêu cầu

- Python 3.8 trở lên
- Các thư viện phụ thuộc được liệt kê trong `requirements.txt`
- FFmpeg (cho xử lý video)
- Tesseract OCR (cho OCR)

### Cài đặt từ mã nguồn

```bash
# Clone repository
git clone https://github.com/yourusername/ai-file-manager.git
cd ai-file-manager

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# Khởi tạo cấu hình và database
python main.py init
```

## Sử dụng

### Khởi tạo

```bash
python main.py init --config-dir ~/.filemanager
```

### Quét và đăng ký file

```bash
python main.py ingest /đường/dẫn/đến/thư/mục --recursive
```

### Tổ chức file theo quy tắc

```bash
python main.py organize --rules ~/.filemanager/rules/default.yaml
```

### Tìm kiếm file

```bash
# Tìm kiếm theo tên file
python main.py search --filename "báo cáo"

# Tìm kiếm theo phần mở rộng
python main.py search --extension pdf

# Tìm kiếm theo nội dung
python main.py search --content "trí tuệ nhân tạo"

# Tìm kiếm vector (ngữ nghĩa)
python main.py search --content "ảnh chụp biển" --vector-search

# Tìm kiếm file trùng lặp
python main.py search --duplicates
```

### Quản lý thẻ

```bash
# Thêm thẻ cho file
python main.py tag --file /đường/dẫn/đến/file.pdf --add "quan trọng"

# Liệt kê thẻ của file
python main.py tag --file /đường/dẫn/đến/file.pdf --list

# Liệt kê tất cả các thẻ
python main.py tag --list-all
```

### Quản lý chỉ mục nội dung

```bash
# Xây dựng lại chỉ mục
python main.py index --rebuild

# Kiểm tra trạng thái chỉ mục
python main.py index --status
```

## Cấu trúc quy tắc

Quy tắc được định nghĩa trong file YAML với cấu trúc sau:

```yaml
rules:
  - name: "Sắp xếp ảnh theo năm và tháng"
    description: "Di chuyển ảnh vào thư mục theo năm và tháng chụp"
    if:
      mimetype: "image/*"
    then:
      move: "/thư/mục/ảnh/{exif.year}/{exif.month}/{filename}"
      tags: ["ảnh", "{exif.year}"]

  - name: "Sắp xếp tài liệu PDF"
    description: "Di chuyển PDF vào thư mục tài liệu"
    if:
      extension: ".pdf"
    then:
      move: "/thư/mục/tài-liệu/{filename}"
      tags: ["tài liệu"]
```

## Cấu trúc dự án

```
ai-file-manager/
├── actions/         # Các hành động (di chuyển, sao chép, gắn thẻ)
├── cli/             # Giao diện dòng lệnh
├── core/            # Các thành phần cốt lõi
├── extractors/      # Trích xuất metadata từ các loại file
├── rules/           # Hệ thống quy tắc
├── search/          # Tìm kiếm và đánh chỉ mục
├── tests/           # Kiểm thử
└── ui/              # Giao diện người dùng (tương lai)
```

## Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request trên GitHub.