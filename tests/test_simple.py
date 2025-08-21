#!/usr/bin/env python3
"""
Test đơn giản cho GameManager logic
Không cần Flask context
"""

import unittest
import sys
import os
import time

# Thêm server directory vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import GameManager, Player, GameRound, Room

class TestGameManagerSimple(unittest.TestCase):
    """Test GameManager logic đơn giản"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.test_room_id = "test_room_123"
        self.test_player_name = "TestPlayer"
        self.test_sid = "test_sid_123"
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_create_room(self):
        """Test tạo phòng"""
        room = self.game_manager.create_room(self.test_room_id, "Test Room")
        
        self.assertIsNotNone(room)
        self.assertEqual(room.id, self.test_room_id)
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.round_number, 1)
        self.assertEqual(len(room.players), 0)
    
    def test_join_room(self):
        """Test tham gia phòng"""
        # Tạo phòng
        self.game_manager.create_room(self.test_room_id, "Test Room")
        
        # Tham gia phòng
        success, message = self.game_manager.join_room(
            self.test_room_id, 
            self.test_player_name, 
            self.test_sid
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Tham gia thành công")
        
        # Kiểm tra người chơi đã được thêm
        room = self.game_manager.rooms[self.test_room_id]
        self.assertIn(self.test_sid, room.players)
        self.assertEqual(room.players[self.test_sid].name, self.test_player_name)
    
    def test_make_guess(self):
        """Test đoán số"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        # Lấy số cần đoán
        room = self.game_manager.rooms[self.test_room_id]
        target_number = room.current_round.number
        
        # Đoán đúng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            target_number
        )
        
        self.assertTrue(success)
        self.assertIn("Chính xác", message)
        self.assertTrue(details['correct'])
        self.assertGreater(details['score_gained'], 0)
    
    def test_reset_room(self):
        """Test reset phòng"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        room = self.game_manager.rooms[self.test_room_id]
        player = room.players[self.test_sid]
        
        # Thêm điểm số
        player.score = 100
        player.streak = 5
        room.scores[self.test_player_name] = 100
        
        # Reset phòng
        success, message = self.game_manager.reset_room(self.test_room_id, self.test_sid)
        
        self.assertTrue(success)
        self.assertEqual(message, "Reset phòng thành công")
        
        # Kiểm tra điểm số đã được reset
        self.assertEqual(player.score, 0)
        self.assertEqual(player.streak, 0)
        self.assertEqual(room.round_number, 1)
        self.assertEqual(len(room.game_history), 0)

if __name__ == '__main__':
    unittest.main()
