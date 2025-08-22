#!/usr/bin/env python3
"""
Test runner đơn giản và ổn định cho tất cả tests
"""

import os
import sys
import unittest
import time

def main():
    """Chạy tất cả tests"""
    print("🚀 Running All Tests for Guess Number Game Server...")
    print("=" * 60)
    
    # Thay đổi thư mục làm việc về thư mục gốc
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Thêm thư mục server vào Python path
    server_dir = os.path.join(project_root, 'server')
    sys.path.insert(0, server_dir)
    print(f"📁 Server path: {server_dir}")
    
    # Tìm và chạy tests
    test_loader = unittest.TestLoader()
    
    print("🔍 Discovering tests...")
    
    # Ưu tiên chạy test đơn giản trước
    simple_tests = []
    other_tests = []
    
    for test_file in os.listdir('tests'):
        if test_file.startswith('test_') and test_file.endswith('.py'):
            if 'simple' in test_file or 'rounds_simple' in test_file:
                simple_tests.append(test_file)
            else:
                other_tests.append(test_file)
    
    print(f"🚀 Simple tests: {simple_tests}")
    print(f"📋 Other tests: {other_tests}")
    
    # Sử dụng unittest.discover để tự động tìm và load tests
    print("🔍 Discovering tests using unittest.discover...")
    discovered_tests = test_loader.discover(
        start_dir='tests',
        pattern='test_*.py',
        top_level_dir=project_root
    )
    
    test_count = discovered_tests.countTestCases()
    print(f"✅ Found {test_count} test cases")
    
    if test_count == 0:
        print("❌ No tests found!")
        return False
    
    # Chạy tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    print("⏱️  Running tests...")
    
    start_time = time.time()
    result = test_runner.run(discovered_tests)
    end_time = time.time()
    
    # Báo cáo kết quả
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    
    print(f"✅ Total tests: {total_tests}")
    print(f"❌ Tests thất bại: {failed_tests}")
    print(f"⚠️  Tests có lỗi: {error_tests}")
    print(f"⏱️  Thời gian: {end_time - start_time:.2f}s")
    
    success_rate = ((total_tests - failed_tests - error_tests) / total_tests * 100) if total_tests > 0 else 0
    print(f"📈 Tỷ lệ thành công: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 Tất cả tests thành công!")
    else:
        print("⚠️  Có tests FAILED hoặc ERROR!")
        
        if result.failures:
            print("\n📋 Failures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n⚠️  Errors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
