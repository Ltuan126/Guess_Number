#!/usr/bin/env python3
"""
Test chat validation và anti-spam cho Guess Number Game Server
"""

import unittest
import sys
import os
import time

# Thêm server directory vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import GameManager, Player, GAME_CONFIG

class TestChatValidation(unittest.TestCase):
    """Test chat validation và anti-spam"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.room = self.game_manager.create_room("test_room", "Test Room")
        self.game_manager.join_room("test_room", "Player", "sid1")
        self.player = self.room.players["sid1"]
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_chat_rate_limit(self):
        """Test giới hạn tần suất chat"""
        # Gửi nhiều tin nhắn
        for i in range(GAME_CONFIG['MAX_CHAT_PER_MINUTE']):
            self.player.add_chat_message()
            # Kiểm tra có thể gửi tin nhắn tiếp theo (trừ lần cuối)
            if i < GAME_CONFIG['MAX_CHAT_PER_MINUTE'] - 1:
                self.assertTrue(self.player.can_send_chat())
        
        # Sau khi gửi MAX_CHAT_PER_MINUTE tin nhắn, không thể gửi thêm
        self.assertFalse(self.player.can_send_chat())
        
        # Tin nhắn thứ MAX_CHAT_PER_MINUTE + 1 sẽ thất bại
        self.player.add_chat_message()
        self.assertFalse(self.player.can_send_chat())
    
    def test_chat_message_cleanup(self):
        """Test dọn dẹp tin nhắn chat cũ"""
        # Thêm tin nhắn cũ (hơn 1 phút)
        old_time = time.time() - 70  # 70 giây trước
        self.player.chat_messages.append(old_time)
        
        # Kiểm tra tin nhắn cũ được dọn dẹp khi gọi can_send_chat
        self.assertTrue(self.player.can_send_chat())
        # Sau khi cleanup, chat_messages sẽ trống vì tin nhắn cũ bị xóa
        self.assertEqual(len(self.player.chat_messages), 0)
    
    def test_player_can_make_guess(self):
        """Test kiểm tra có thể đoán số không"""
        # Lần đầu đoán sẽ thành công
        self.assertTrue(self.player.can_make_guess())
        
        # Đoán một lần
        self.game_manager.make_guess("test_room", "sid1", 50)
        
        # Đoán ngay lập tức sẽ thất bại
        self.assertFalse(self.player.can_make_guess())
        
        # Chờ đủ thời gian rate limit
        time.sleep(GAME_CONFIG['RATE_LIMIT_MS'] / 1000 + 0.1)
        
        # Đoán lại sẽ thành công
        self.assertTrue(self.player.can_make_guess())
    
    def test_chat_basic_logic(self):
        """Test logic cơ bản của chat"""
        # Ban đầu có thể gửi chat
        self.assertTrue(self.player.can_send_chat())
        
        # Gửi 1 tin nhắn
        self.player.add_chat_message()
        self.assertTrue(self.player.can_send_chat())
        
        # Gửi thêm tin nhắn để kiểm tra giới hạn
        for i in range(GAME_CONFIG['MAX_CHAT_PER_MINUTE'] - 1):
            self.player.add_chat_message()
        
        # Sau khi gửi đủ MAX_CHAT_PER_MINUTE tin nhắn
        self.assertFalse(self.player.can_send_chat())

if __name__ == '__main__':
    unittest.main()
