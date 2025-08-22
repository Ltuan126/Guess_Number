import unittest
import time
import sys
import os

# Thêm server directory vào path để import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import GameManager, Player, GameRound, Room, GAME_CONFIG

class TestGameManager(unittest.TestCase):
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
        """Test tạo phòng mới"""
        room = self.game_manager.create_room(
            self.test_room_id, 
            "Test Room", 
            max_players=5
        )
        
        self.assertIsNotNone(room)
        self.assertEqual(room.id, self.test_room_id)
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.max_players, 5)
        self.assertTrue(room.is_active)
        self.assertEqual(room.round_number, 1)
        self.assertIsInstance(room.current_round, GameRound)
    
    def test_create_room_duplicate_id(self):
        """Test tạo phòng với ID đã tồn tại"""
        # Tạo phòng đầu tiên
        self.game_manager.create_room(self.test_room_id, "First Room")
        
        # Thử tạo phòng thứ hai với cùng ID
        room2 = self.game_manager.create_room(self.test_room_id, "Second Room")
        
        self.assertIsNone(room2)
    
    def test_create_room_max_limit(self):
        """Test giới hạn số lượng phòng tối đa"""
        # Tạo đủ số phòng tối đa
        for i in range(GAME_CONFIG['MAX_ROOMS']):
            room_id = f"test_room_{i}"
            self.game_manager.create_room(room_id, f"Room {i}")
        
        # Thử tạo phòng thêm
        extra_room = self.game_manager.create_room("extra_room", "Extra Room")
        self.assertIsNone(extra_room)
    
    def test_join_room_success(self):
        """Test tham gia phòng thành công"""
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
        
        # Kiểm tra người chơi đã được thêm vào phòng
        room = self.game_manager.rooms[self.test_room_id]
        self.assertIn(self.test_sid, room.players)
        self.assertEqual(room.players[self.test_sid].name, self.test_player_name)
    
    def test_join_room_not_exists(self):
        """Test tham gia phòng không tồn tại"""
        success, message = self.game_manager.join_room(
            "non_existent_room", 
            self.test_player_name, 
            self.test_sid
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Phòng không tồn tại")
    
    def test_join_room_with_password(self):
        """Test tham gia phòng có mật khẩu"""
        # Tạo phòng private với mật khẩu
        self.game_manager.create_room(
            self.test_room_id, 
            "Private Room", 
            password="secret123", 
            is_private=True
        )
        
        # Thử tham gia không có mật khẩu
        success, message = self.game_manager.join_room(
            self.test_room_id, 
            self.test_player_name, 
            self.test_sid
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Mật khẩu không đúng")
        
        # Tham gia với mật khẩu đúng
        success, message = self.game_manager.join_room(
            self.test_room_id, 
            self.test_player_name, 
            self.test_sid, 
            "secret123"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Tham gia thành công")
    
    def test_join_room_duplicate_name(self):
        """Test tham gia phòng với tên đã tồn tại"""
        # Tạo phòng và thêm người chơi đầu tiên
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, "sid1")
        
        # Thử tham gia với tên đã tồn tại
        success, message = self.game_manager.join_room(
            self.test_room_id, 
            self.test_player_name, 
            "sid2"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Tên người chơi đã tồn tại")
    
    def test_join_room_max_players(self):
        """Test giới hạn số lượng người chơi trong phòng"""
        # Tạo phòng với giới hạn 2 người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room", max_players=2)
        
        # Thêm 2 người chơi đầu tiên
        self.game_manager.join_room(self.test_room_id, "Player1", "sid1")
        self.game_manager.join_room(self.test_room_id, "Player2", "sid2")
        
        # Thử thêm người chơi thứ 3
        success, message = self.game_manager.join_room(
            self.test_room_id, 
            "Player3", 
            "sid3"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Phòng đã đầy")
    
    def test_leave_room(self):
        """Test rời phòng"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        # Rời phòng
        self.game_manager.leave_room(self.test_sid)
        
        # Kiểm tra người chơi đã được xóa
        room = self.game_manager.rooms[self.test_room_id]
        self.assertNotIn(self.test_sid, room.players)
        self.assertNotIn(self.test_sid, self.game_manager.player_rooms)
    
    def test_make_guess_correct(self):
        """Test đoán số đúng"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        room = self.game_manager.rooms[self.test_room_id]
        secret_number = room.current_round.number
        
        # Đoán số đúng
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            secret_number
        )
        
        self.assertTrue(success)
        self.assertIn("Chính xác", message)
        self.assertTrue(details['correct'])
        self.assertGreater(details['score_gained'], 0)
        
        # Kiểm tra điểm số đã được cập nhật
        player = room.players[self.test_sid]
        self.assertGreater(player.score, 0)
        self.assertEqual(player.correct_guesses, 1)
        self.assertEqual(player.streak, 1)
    
    def test_make_guess_incorrect(self):
        """Test đoán số sai"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        room = self.game_manager.rooms[self.test_room_id]
        secret_number = room.current_round.number
        
        # Đoán số sai (thấp hơn) - đảm bảo không âm
        wrong_guess = max(1, secret_number - 10)
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            wrong_guess
        )
        
        self.assertTrue(success)
        self.assertIn("lớn hơn", message)
        self.assertFalse(details['correct'])
        
        # Kiểm tra streak đã bị reset
        player = room.players[self.test_sid]
        self.assertEqual(player.streak, 0)
    
    def test_make_guess_rate_limit(self):
        """Test giới hạn tốc độ đoán"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        room = self.game_manager.rooms[self.test_room_id]
        secret_number = room.current_round.number
        
        # Đoán lần đầu
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            secret_number - 1
        )
        
        self.assertTrue(success)
        
        # Đoán ngay lập tức (vi phạm rate limit)
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            secret_number + 1
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Đoán quá nhanh, vui lòng chờ")
    
    def test_make_guess_out_of_range(self):
        """Test đoán số ngoài phạm vi"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        # Đoán số ngoài phạm vi
        success, message, details = self.game_manager.make_guess(
            self.test_room_id, 
            self.test_sid, 
            999  # Số rất lớn
        )
        
        self.assertFalse(success)
        self.assertIn("Số phải trong khoảng", message)
    
    def test_reset_room(self):
        """Test reset phòng"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        room = self.game_manager.rooms[self.test_room_id]
        player = room.players[self.test_sid]
        
        # Thêm một số điểm
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
    
    def test_get_room_info(self):
        """Test lấy thông tin phòng"""
        # Tạo phòng và thêm người chơi
        self.game_manager.create_room(self.test_room_id, "Test Room")
        self.game_manager.join_room(self.test_room_id, self.test_player_name, self.test_sid)
        
        # Lấy thông tin phòng
        room_info = self.game_manager.get_room_info(self.test_room_id)
        
        self.assertIsNotNone(room_info)
        self.assertEqual(room_info['id'], self.test_room_id)
        self.assertEqual(room_info['name'], "Test Room")
        self.assertEqual(room_info['round_number'], 1)
        self.assertEqual(len(room_info['players']), 1)
        self.assertEqual(room_info['players'][0]['name'], self.test_player_name)
    
    def test_get_available_rooms(self):
        """Test lấy danh sách phòng có sẵn"""
        # Tạo một số phòng
        self.game_manager.create_room("public_room", "Public Room")
        self.game_manager.create_room("private_room", "Private Room", password="secret", is_private=True)
        
        # Lấy danh sách phòng có sẵn
        available_rooms = self.game_manager.get_available_rooms()
        
        # Chỉ phòng public mới hiển thị
        room_ids = [room['id'] for room in available_rooms]
        self.assertIn("public_room", room_ids)
        self.assertNotIn("private_room", room_ids)
    
    def test_cleanup_inactive_rooms(self):
        """Test dọn dẹp phòng không hoạt động"""
        # Tạo phòng
        self.game_manager.create_room(self.test_room_id, "Test Room")
        
        # Đánh dấu phòng không hoạt động
        room = self.game_manager.rooms[self.test_room_id]
        room.is_active = False
        room.created_at = time.time() - 700  # 700 giây trước
        
        # Chạy cleanup (giả lập)
        current_time = time.time()
        inactive_rooms = []
        
        for room_id, room_obj in self.game_manager.rooms.items():
            if not room_obj.is_active and (current_time - room_obj.created_at) > 600:
                inactive_rooms.append(room_id)
        
        # Kiểm tra phòng đã được đánh dấu để xóa
        self.assertIn(self.test_room_id, inactive_rooms)

if __name__ == '__main__':
    unittest.main()
