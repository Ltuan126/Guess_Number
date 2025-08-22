import unittest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Thêm server directory vào path để import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server import app, socketio, game_manager

class TestSocketEvents(unittest.TestCase):
    def setUp(self):
        """Khởi tạo test environment"""
        # Tạo Flask app context
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Tạo request context
        self.client = app.test_client()
        self.request_context = app.test_request_context()
        self.request_context.push()
        
        # Reset game manager
        game_manager.rooms.clear()
        game_manager.player_rooms.clear()
        
        # Mock socketio emit
        self.emit_mock = Mock()
        self.socketio_emit_mock = Mock()
        
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(game_manager.rooms.keys()):
            if room_id.startswith('test_'):
                game_manager.delete_room(room_id)
        
        # Pop contexts
        self.request_context.pop()
        self.app_context.pop()
    
    @patch('server.emit')
    def test_connect_event(self, mock_emit):
        """Test sự kiện connect"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Gọi event handler
            from server import on_connect
            on_connect()
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once_with('connected', {'sid': 'test_sid_123'})
    
    @patch('server.game_manager.leave_room')
    def test_disconnect_event(self, mock_leave_room):
        """Test sự kiện disconnect"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Gọi event handler
            from server import on_disconnect
            on_disconnect()
            
            # Kiểm tra leave_room đã được gọi
            mock_leave_room.assert_called_once_with('test_sid_123')
    
    @patch('server.emit')
    @patch('server.join_room')
    @patch('server.socketio.emit')
    def test_join_room_success(self, mock_socketio_emit, mock_join_room, mock_emit):
        """Test tham gia phòng thành công"""
        # Tạo phòng test
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': room_id,
                'player_name': 'TestPlayer',
                'password': None
            }
            
            # Gọi event handler
            from server import on_join_room
            on_join_room(data)
            
            # Kiểm tra join_room đã được gọi
            mock_join_room.assert_called_once_with(room_id)
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[0]
            self.assertEqual(call_args[0], 'room_joined')
            self.assertEqual(call_args[1]['room_id'], room_id)
            self.assertEqual(call_args[1]['player_name'], 'TestPlayer')
            
            # Kiểm tra socketio.emit đã được gọi
            mock_socketio_emit.assert_called_once()
            call_args = mock_socketio_emit.call_args[0]
            self.assertEqual(call_args[0], 'player_joined')
            self.assertEqual(call_args[1]['room_id'], room_id)
    
    @patch('server.emit')
    def test_join_room_error(self, mock_emit):
        """Test tham gia phòng thất bại"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data với room_id rỗng
            data = {
                'room_id': '',
                'player_name': 'TestPlayer',
                'password': None
            }
            
            # Gọi event handler
            from server import on_join_room
            on_join_room(data)
            
            # Kiểm tra emit error đã được gọi
            mock_emit.assert_called_once_with('join_error', {'error': 'ID phòng không được để trống'})
    
    @patch('server.emit')
    def test_leave_room(self, mock_emit):
        """Test rời phòng"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Gọi event handler
            from server import on_leave_room
            on_leave_room()
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once_with('room_left', {'message': 'Đã rời phòng'})
    
    @patch('server.emit')
    @patch('server.socketio.emit')
    def test_make_guess_success(self, mock_socketio_emit, mock_emit):
        """Test đoán số thành công"""
        # Tạo phòng và thêm người chơi
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        game_manager.join_room(room_id, "TestPlayer", "test_sid_123")
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': room_id,
                'guess': '50'
            }
            
            # Gọi event handler
            from server import on_make_guess
            on_make_guess(data)
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[0]
            self.assertEqual(call_args[0], 'guess_result')
            self.assertIn('message', call_args[1])
            self.assertIn('details', call_args[1])
    
    @patch('server.emit')
    def test_make_guess_invalid_number(self, mock_emit):
        """Test đoán số với số không hợp lệ"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data với số không hợp lệ
            data = {
                'room_id': 'test_room',
                'guess': 'invalid'
            }
            
            # Gọi event handler
            from server import on_make_guess
            on_make_guess(data)
            
            # Kiểm tra emit error đã được gọi
            mock_emit.assert_called_once_with('guess_error', {'error': 'Số không hợp lệ'})
    
    @patch('server.socketio.emit')
    def test_chat_message(self, mock_socketio_emit):
        """Test gửi tin nhắn chat"""
        # Tạo phòng và thêm người chơi
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        game_manager.join_room(room_id, "TestPlayer", "test_sid_123")
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': room_id,
                'message': 'Hello World!'
            }
            
            # Gọi event handler
            from server import on_chat_message
            on_chat_message(data)
            
            # Kiểm tra socketio.emit đã được gọi
            mock_socketio_emit.assert_called_once()
            call_args = mock_socketio_emit.call_args[0]
            self.assertEqual(call_args[0], 'chat_message')
            self.assertEqual(call_args[1]['room_id'], room_id)
            self.assertEqual(call_args[1]['message'], 'Hello World!')
            self.assertEqual(call_args[1]['player_name'], 'TestPlayer')
    
    @patch('server.emit')
    @patch('server.socketio.emit')
    def test_reset_room_success(self, mock_socketio_emit, mock_emit):
        """Test reset phòng thành công"""
        # Tạo phòng và thêm người chơi
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        game_manager.join_room(room_id, "TestPlayer", "test_sid_123")
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': room_id
            }
            
            # Gọi event handler
            from server import on_reset_room
            on_reset_room(data)
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[0]
            self.assertEqual(call_args[0], 'room_reset')
            self.assertEqual(call_args[1]['message'], 'Reset phòng thành công')
            
            # Kiểm tra socketio.emit đã được gọi 2 lần:
            # 1. new_round (từ _start_new_round)
            # 2. room_reset (từ on_reset_room)
            self.assertEqual(mock_socketio_emit.call_count, 2)
            
            # Kiểm tra các event đã được gọi
            calls = mock_socketio_emit.call_args_list
            event_names = [call[0][0] for call in calls]
            self.assertIn('new_round', event_names)
            self.assertIn('room_reset', event_names)
    
    @patch('server.emit')
    def test_get_room_info_success(self, mock_emit):
        """Test lấy thông tin phòng thành công"""
        # Tạo phòng và thêm người chơi
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        game_manager.join_room(room_id, "TestPlayer", "test_sid_123")
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': room_id
            }
            
            # Gọi event handler
            from server import on_get_room_info
            on_get_room_info(data)
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[0]
            self.assertEqual(call_args[0], 'room_info')
            self.assertEqual(call_args[1]['id'], room_id)
            self.assertEqual(call_args[1]['name'], 'Test Room')
    
    @patch('server.emit')
    def test_get_room_info_not_exists(self, mock_emit):
        """Test lấy thông tin phòng không tồn tại"""
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Mock data
            data = {
                'room_id': 'non_existent_room'
            }
            
            # Gọi event handler
            from server import on_get_room_info
            on_get_room_info(data)
            
            # Kiểm tra emit error đã được gọi
            mock_emit.assert_called_once_with('room_info_error', {'error': 'Phòng không tồn tại'})
    
    @patch('server.emit')
    def test_get_available_rooms(self, mock_emit):
        """Test lấy danh sách phòng có sẵn"""
        # Tạo một số phòng
        game_manager.create_room("public_room", "Public Room")
        game_manager.create_room("private_room", "Private Room", password="secret", is_private=True)
        
        # Mock request.sid
        with patch('server.request') as mock_request:
            mock_request.sid = "test_sid_123"
            
            # Gọi event handler
            from server import on_get_available_rooms
            on_get_available_rooms()
            
            # Kiểm tra emit đã được gọi
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args[0]
            self.assertEqual(call_args[0], 'available_rooms')
            self.assertIn('rooms', call_args[1])
            
            # Kiểm tra chỉ phòng public mới hiển thị
            rooms = call_args[1]['rooms']
            room_ids = [room['id'] for room in rooms]
            self.assertIn("public_room", room_ids)
            self.assertNotIn("private_room", room_ids)

class TestAPIRoutes(unittest.TestCase):
    def setUp(self):
        """Khởi tạo test environment"""
        # Tạo Flask app context
        self.app_context = app.app_context()
        self.app_context.push()
        
        self.app = app.test_client()
        self.app.testing = True
        
        # Reset game manager
        game_manager.rooms.clear()
        game_manager.player_rooms.clear()
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        # Xóa tất cả phòng test
        for room_id in list(game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                game_manager.delete_room(room_id)
        
        # Pop Flask app context
        self.app_context.pop()
    
    def test_home_route(self):
        """Test route trang chủ"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Guess Number Server v2.0')
        self.assertEqual(data['status'], 'running')
        self.assertEqual(data['version'], '2.0.0')
        self.assertIn('timestamp', data)
    
    def test_get_rooms_api(self):
        """Test API lấy danh sách phòng"""
        # Tạo một số phòng
        game_manager.create_room("test_room_1", "Room 1")
        game_manager.create_room("test_room_2", "Room 2")
        
        response = self.app.get('/api/rooms')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('rooms', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['rooms']), 2)
    
    def test_get_room_info_api(self):
        """Test API lấy thông tin phòng"""
        # Tạo phòng
        room_id = "test_room_123"
        game_manager.create_room(room_id, "Test Room")
        
        response = self.app.get(f'/api/rooms/{room_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], room_id)
        self.assertEqual(data['name'], 'Test Room')
    
    def test_get_room_info_not_exists(self):
        """Test API lấy thông tin phòng không tồn tại"""
        response = self.app.get('/api/rooms/non_existent_room')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Phòng không tồn tại')
    
    def test_create_room_api_success(self):
        """Test API tạo phòng thành công"""
        data = {
            'room_id': 'test_room_123',
            'room_name': 'Test Room',
            'max_players': 5
        }
        
        response = self.app.post('/api/rooms', 
                               data=json.dumps(data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('room', response_data)
        self.assertEqual(response_data['room']['id'], 'test_room_123')
    
    def test_create_room_api_missing_id(self):
        """Test API tạo phòng thiếu ID"""
        data = {
            'room_name': 'Test Room',
            'max_players': 5
        }
        
        response = self.app.post('/api/rooms', 
                               data=json.dumps(data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'ID phòng không được để trống')

if __name__ == '__main__':
    unittest.main()
