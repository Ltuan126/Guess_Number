#!/usr/bin/env python3
"""
Test validation input và anti-spam cho Guess Number Game Server
"""

import unittest
import sys
import os
import time

# Thêm server directory vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import GameManager, GAME_CONFIG

class TestInputValidation(unittest.TestCase):
    """Test validation input"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_create_room_validation(self):
        """Test validation khi tạo phòng"""
        # Test room_id rỗng
        room = self.game_manager.create_room("", "Test Room")
        self.assertIsNone(room)
        
        # Test room_id quá ngắn
        room = self.game_manager.create_room("ab", "Test Room")
        self.assertIsNone(room)
        
        # Test room_id hợp lệ
        room = self.game_manager.create_room("test_room_123", "Test Room")
        self.assertIsNotNone(room)
    
    def test_join_room_validation(self):
        """Test validation khi tham gia phòng"""
        # Tạo phòng test
        room = self.game_manager.create_room("test_room", "Test Room")
        
        # Test player_name quá ngắn
        success, message = self.game_manager.join_room("test_room", "a", "sid1")
        self.assertFalse(success)
        
        # Test player_name hợp lệ
        success, message = self.game_manager.join_room("test_room", "Player_123", "sid1")
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
