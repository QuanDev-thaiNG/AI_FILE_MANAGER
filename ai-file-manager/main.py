#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI File Manager - Công cụ quản lý và sắp xếp tập tin thông minh

Chương trình này giúp quản lý, phân loại và tổ chức các tập tin dựa trên
quy tắc thông minh, trích xuất metadata và nội dung, cùng với khả năng
tìm kiếm nâng cao.
"""

import sys
from cli.commands import main as cli_main

def main():
    """Hàm chính của chương trình"""
    return cli_main()

if __name__ == "__main__":
    sys.exit(main())