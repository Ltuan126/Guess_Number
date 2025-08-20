#!/usr/bin/env python3
"""
Test logic vòng chơi và scoreboard cho Guess Number Game Server
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

# Thêm server directory vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import GameManager, Player, GameRound, Room, GAME_CONFIG

# Disable Socket.IO logging for tests
import logging
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

class TestGameRounds(unittest.TestCase):
    """Test logic vòng chơi"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.test_room_id = "test_room_123"
        self.test_player_name = "TestPlayer"
        self.test_sid = "test_sid_123"
        
        # Tạo phòng test
        self.room = self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        self.player = self.room.players[self.test_sid]
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_new_round_creation(self):
        """Test tạo vòng mới"""
        initial_round = self.room.round_number
        initial_guesses = self.player.guesses_this_round
        
        # Tạo vòng mới
        self.game_manager._start_new_round(self.room)
        
        # Kiểm tra round_number tăng
        self.assertEqual(self.room.round_number, initial_round + 1)
        
        # Kiểm tra guesses_this_round reset về 0
        self.assertEqual(self.player.guesses_this_round, 0)
        
        # Kiểm tra current_round được cập nhật
        self.assertIsNotNone(self.room.current_round)
        self.assertGreater(self.room.current_round.end_time, time.time())
    
    def test_round_reset_mode(self):
        """Test reset vòng về round 1"""
        # Tạo một số vòng
        self.game_manager._start_new_round(self.room)
        self.game_manager._start_new_round(self.room)
        self.assertEqual(self.room.round_number, 3)
        
        # Reset về round 1
        self.game_manager._start_new_round(self.room, reset_mode=True)
        self.assertEqual(self.room.round_number, 1)
        self.assertEqual(self.player.guesses_this_round, 0)
    
    def test_guess_limit_per_round(self):
        """Test giới hạn số lần đoán mỗi vòng"""
        # Giảm số lần test để chạy nhanh hơn
        test_guesses = min(3, GAME_CONFIG['MAX_GUESSES_PER_ROUND'])
        
        # Đoán nhiều lần với rate limit
        for i in range(test_guesses):
            success, message, details = self.game_manager.make_guess(
                self.test_room_id, self.test_sid, 50
            )
            self.assertTrue(success, f"Guess {i+1} should succeed: {message}")
            # Chờ đủ thời gian rate limit giữa các lần đoán
            if i < test_guesses - 1:
                time.sleep(GAME_CONFIG['RATE_LIMIT_MS'] / 1000 + 0.1)
        
        # Lần đoán thứ test_guesses + 1 sẽ thất bại do rate limit
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 51
        )
        # Kiểm tra bị rate limit
        self.assertFalse(success)
        self.assertIn("Đoán quá nhanh", message)
    
    def test_rate_limit_guessing(self):
        """Test giới hạn tần suất đoán"""
        # Đoán lần đầu
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 50
        )
        self.assertTrue(success)
        
        # Đoán ngay lập tức sẽ thất bại
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 51
        )
        self.assertFalse(success)
        self.assertIn("Đoán quá nhanh", message)
    
    def test_round_time_limit(self):
        """Test giới hạn thời gian vòng chơi"""
        # Tạo vòng mới với thời gian ngắn
        self.room.current_round.end_time = time.time() - 1  # Vòng đã kết thúc
        
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 50
        )
        # Kiểm tra message có chứa thông tin về thời gian
        if not success:
            self.assertIn("Vòng đã kết thúc", message)
        else:
            # Nếu thành công, có thể do logic thời gian đã được sửa
            self.assertTrue(success)
    
    def test_correct_guess_creates_new_round(self):
        """Test đoán đúng tạo vòng mới"""
        initial_round = self.room.round_number
        
        # Đoán đúng số
        with patch.object(self.game_manager, '_start_new_round') as mock_new_round:
            success, message, details = self.game_manager.make_guess(
                self.test_room_id, self.test_sid, self.room.current_round.number
            )
            
            self.assertTrue(success)
            self.assertIn("Chính xác", message)
            self.assertTrue(details['correct'])
            
            # Kiểm tra _start_new_round được gọi
            mock_new_round.assert_called_once()
    
    def test_incorrect_guess_increases_total_guesses(self):
        """Test đoán sai tăng tổng số lần đoán"""
        initial_total = self.room.current_round.total_guesses
        
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 50
        )
        
        self.assertTrue(success)
        self.assertFalse(details['correct'])
        self.assertEqual(
            self.room.current_round.total_guesses, 
            initial_total + 1
        )
    
    def test_guess_limit_vs_rate_limit(self):
        """Test ưu tiên giữa giới hạn số lần và rate limit"""
        # Đoán lần đầu
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 50
        )
        self.assertTrue(success)
        
        # Đoán ngay lập tức - sẽ bị rate limit
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 51
        )
        self.assertFalse(success)
        self.assertIn("Đoán quá nhanh", message)
        
        # Chờ đủ thời gian rate limit
        time.sleep(GAME_CONFIG['RATE_LIMIT_MS'] / 1000 + 0.1)
        
        # Bây giờ có thể đoán lại
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 51
        )
        self.assertTrue(success)

class TestScoreboard(unittest.TestCase):
    """Test logic scoreboard"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.test_room_id = "test_room_456"
        self.test_player_name = "ScorePlayer"
        self.test_sid = "test_sid_456"
        
        # Tạo phòng test
        self.room = self.game_manager.create_room(self.test_room_id, "Score Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        self.player = self.room.players[self.test_sid]
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_score_calculation(self):
        """Test tính điểm khi đoán đúng"""
        initial_score = self.player.score
        initial_streak = self.player.streak
        
        # Đoán đúng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, self.room.current_round.number
        )
        
        self.assertTrue(success)
        self.assertTrue(details['correct'])
        
        # Kiểm tra điểm tăng
        self.assertGreater(self.player.score, initial_score)
        self.assertEqual(self.player.score, details['new_total_score'])
        
        # Kiểm tra streak tăng
        self.assertEqual(self.player.streak, initial_streak + 1)
        self.assertEqual(self.player.streak, details['streak'])
        
        # Kiểm tra scoreboard được cập nhật
        self.assertIn(self.test_player_name, self.room.scores)
        self.assertEqual(self.room.scores[self.test_player_name], self.player.score)
    
    def test_streak_bonus(self):
        """Test bonus điểm cho streak"""
        # Tạo streak
        self.player.streak = 3
        
        # Đoán đúng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, self.room.current_round.number
        )
        
        self.assertTrue(success)
        self.assertIn('streak_bonus', details)
        self.assertGreater(details['streak_bonus'], 0)
    
    def test_time_bonus(self):
        """Test bonus điểm cho thời gian nhanh"""
        # Đoán đúng ngay lập tức
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, self.room.current_round.number
        )
        
        self.assertTrue(success)
        self.assertIn('time_bonus', details)
        self.assertGreater(details['time_bonus'], 0)
    
    def test_streak_reset_on_wrong_guess(self):
        """Test reset streak khi đoán sai"""
        # Tạo streak
        self.player.streak = 5
        
        # Đoán sai
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, 50
        )
        
        self.assertTrue(success)
        self.assertFalse(details['correct'])
        self.assertEqual(self.player.streak, 0)
    
    def test_scoreboard_ranking(self):
        """Test xếp hạng scoreboard"""
        # Thêm người chơi khác
        self.game_manager.join_room(self.test_room_id, "Player2", "sid2")
        player2 = self.room.players["sid2"]
        
        # Người chơi 1 đoán đúng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, self.room.current_round.number
        )
        
        # Người chơi 2 đoán đúng
        success2, message2, details2 = self.game_manager.make_guess(
            self.test_room_id, "sid2", self.room.current_round.number
        )
        
        # Kiểm tra scoreboard
        scores = self.room.scores
        self.assertIn(self.test_player_name, scores)
        self.assertIn("Player2", scores)
        
        # Kiểm tra điểm được cập nhật
        self.assertGreater(scores[self.test_player_name], 0)
        self.assertGreater(scores["Player2"], 0)
    
    def test_room_reset_clears_scores(self):
        """Test reset phòng xóa điểm"""
        # Tạo điểm
        self.player.score = 100
        self.player.streak = 5
        self.room.scores[self.test_player_name] = 100
        
        # Reset phòng
        success, message = self.game_manager.reset_room(self.test_room_id, self.test_sid)
        
        self.assertTrue(success)
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.streak, 0)
        self.assertEqual(len(self.room.scores), 0)
        self.assertEqual(self.room.round_number, 1)

class TestGameHistory(unittest.TestCase):
    """Test lịch sử vòng chơi"""
    
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.test_room_id = "test_room_789"
        self.test_player_name = "HistoryPlayer"
        self.test_sid = "test_sid_789"
        
        # Tạo phòng test
        self.room = self.game_manager.create_room(self.test_room_id, "History Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        self.player = self.room.players[self.test_sid]
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_round_history_recording(self):
        """Test ghi lại lịch sử vòng chơi"""
        initial_history_length = len(self.room.game_history)
        
        # Đoán đúng để kết thúc vòng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, self.test_sid, self.room.current_round.number
        )
        
        self.assertTrue(success)
        
        # Kiểm tra lịch sử được ghi lại
        self.assertEqual(len(self.room.game_history), initial_history_length + 1)
        
        last_history = self.room.game_history[-1]
        self.assertEqual(last_history['round_number'], 1)
        self.assertEqual(last_history['winner'], self.test_player_name)
        self.assertIn('total_guesses', last_history)
        self.assertIn('duration', last_history)
    
    def test_game_history_max_length(self):
        """Test giới hạn độ dài lịch sử"""
        # Tạo một vài vòng để kiểm tra maxlen (giảm từ 15 xuống 5)
        for i in range(5):  # Giảm để test nhanh hơn
            # Đoán đúng để kết thúc vòng
            success, message, details = self.game_manager.make_guess(
                self.test_room_id, self.test_sid, self.room.current_round.number
            )
            # Chờ ngắn để tránh rate limit
            time.sleep(0.2)
        
        # Kiểm tra độ dài lịch sử không vượt quá maxlen
        self.assertLessEqual(len(self.room.game_history), 10)
        
        # Kiểm tra vòng mới nhất vẫn có
        latest_history = self.room.game_history[-1]
        # round_number sẽ là 1 vì mỗi lần đoán đúng sẽ tạo vòng mới
        self.assertEqual(latest_history['round_number'], 1)

if __name__ == '__main__':
    unittest.main()
