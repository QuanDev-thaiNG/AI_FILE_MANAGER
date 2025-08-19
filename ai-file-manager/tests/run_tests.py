#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script để chạy tất cả các bài kiểm thử

Sử dụng:
    python run_tests.py
"""

import unittest
import sys
import os

def run_all_tests():
    """Chạy tất cả các bài kiểm thử trong thư mục tests"""
    # Tìm tất cả các bài kiểm thử
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    
    # Chạy các bài kiểm thử
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Trả về mã thoát dựa trên kết quả kiểm thử
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name):
    """Chạy một bài kiểm thử cụ thể
    
    Args:
        test_name: Tên của file kiểm thử (không có phần mở rộng .py)
    """
    # Tìm bài kiểm thử cụ thể
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern=f"{test_name}.py")
    
    # Chạy bài kiểm thử
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Trả về mã thoát dựa trên kết quả kiểm thử
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Chạy bài kiểm thử cụ thể
        test_name = sys.argv[1]
        sys.exit(run_specific_test(test_name))
    else:
        # Chạy tất cả các bài kiểm thử
        sys.exit(run_all_tests())