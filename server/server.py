import logging
import os
import json
import time
import random
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms as socket_rooms
from flask_cors import CORS
# import eventlet  # Commented out for Python 3.13+ compatibility

# Cấu hình logging
import os
from pathlib import Path

# Tạo thư mục logs nếu chưa có
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'game_server.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'guess_number_secret_key_2024')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Cấu hình game
GAME_CONFIG = {
    'RANGE_DEFAULT': (1, 100),
    'ROUND_TIME': 300,  # 5 minutes - tăng thời gian vòng chơi
    'MAX_PLAYERS_PER_ROOM': 20,
    'MAX_ROOMS': 100,
    'RATE_LIMIT_MS': 1000,  # 1 second between guesses
    'MAX_CHAT_LENGTH': 200,
    'SCORE_CORRECT': 10,
    'SCORE_BONUS_TIME': 5, # bonus for quick guess
    'SCORE_STREAK_MULTIPLIER': 1.5,
    # Anti-spam settings
    'MAX_GUESSES_PER_ROUND': 50,  # max guesses per round per player
    'MAX_CHAT_PER_MINUTE': 10,    # max chat messages per minute per player
    'MIN_PLAYER_NAME_LENGTH': 2,
    'MAX_PLAYER_NAME_LENGTH': 20,
    'MIN_ROOM_ID_LENGTH': 3,
    'MAX_ROOM_ID_LENGTH': 30,
    'MIN_ROOM_NAME_LENGTH': 3,
    'MAX_ROOM_NAME_LENGTH': 50
}

@dataclass
class Player:
    name: str
    sid: str
    joined_at: float
    last_guess_at: float
    score: int = 0
    streak: int = 0
    total_guesses: int = 0
    correct_guesses: int = 0
    guesses_this_round: int = 0
    chat_messages: deque = None
    last_chat_time: float = 0

    def __post_init__(self):
        if self.chat_messages is None:
            self.chat_messages = deque(maxlen=GAME_CONFIG['MAX_CHAT_PER_MINUTE'])

    def can_make_guess(self) -> bool:
        """Kiểm tra có thể đoán số không"""
        current_time = time.time()
        time_limit = GAME_CONFIG['RATE_LIMIT_MS'] / 1000
        return (current_time - self.last_guess_at >= time_limit and
                self.guesses_this_round < GAME_CONFIG['MAX_GUESSES_PER_ROUND'])

    def can_send_chat(self) -> bool:
        """Kiểm tra có thể gửi chat không"""
        current_time = time.time()
        # Xóa tin nhắn cũ hơn 1 phút
        while (self.chat_messages and
               current_time - self.chat_messages[0] > 60):
            self.chat_messages.popleft()

        return len(self.chat_messages) < GAME_CONFIG['MAX_CHAT_PER_MINUTE']

    def add_chat_message(self):
        """Thêm tin nhắn chat mới"""
        current_time = time.time()
        self.chat_messages.append(current_time)
        self.last_chat_time = current_time

@dataclass
class GameRound:
    number: int
    range_low: int
    range_high: int
    start_time: float
    end_time: float
    winner: Optional[str] = None
    total_guesses: int = 0

@dataclass
class Room:
    id: str
    name: str
    created_at: float
    current_round: GameRound
    players: Dict[str, Player]
    scores: Dict[str, int]
    round_number: int
    is_active: bool
    max_players: int
    password: Optional[str] = None
    is_private: bool = False
    game_history: deque = None
    last_activity: float = 0 # Thêm trường để theo dõi hoạt động gần đây

    def __post_init__(self):
        if self.game_history is None:
            self.game_history = deque(maxlen=10)
        self.last_activity = time.time() # Khởi tạo khi tạo phòng

class GameManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player_rooms: Dict[str, str] = {}  # sid -> room_id
        self.cleanup_thread = None
        self.persistence_file = Path(__file__).parent / 'game_data.json'
        self.load_rooms_from_file()  # Load rooms từ file khi khởi động
        self.start_cleanup_thread()

    def save_rooms_to_file(self):
        """Lưu rooms vào file JSON"""
        try:
            # Chuyển đổi rooms thành dict có thể serialize
            rooms_data = {}
            for room_id, room in self.rooms.items():
                # Chỉ lưu rooms có người chơi hoặc mới tạo gần đây
                if len(room.players) > 0 or (time.time() - room.created_at) < 3600:  # 1 giờ
                    room_dict = asdict(room)
                    # Chuyển đổi datetime objects thành timestamp
                    room_dict['created_at'] = room.created_at
                    room_dict['last_activity'] = room.last_activity
                    if room.current_round:
                        room_dict['current_round'] = asdict(room.current_round)
                        room_dict['current_round']['start_time'] = room.current_round.start_time
                        room_dict['current_round']['end_time'] = room.current_round.end_time
                    rooms_data[room_id] = room_dict
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(rooms_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(rooms_data)} rooms to file")
        except Exception as e:
            logger.error(f"Error saving rooms to file: {e}")

    def load_rooms_from_file(self):
        """Load rooms từ file JSON"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    rooms_data = json.load(f)
                
                for room_id, room_dict in rooms_data.items():
                    try:
                        # Tạo lại Room object từ data
                        room = Room(
                            id=room_dict['id'],
                            name=room_dict['name'],
                            max_players=room_dict['max_players'],
                            password=room_dict.get('password'),
                            is_private=room_dict.get('is_private', False),
                            created_at=room_dict['created_at'],
                            last_activity=room_dict['last_activity']
                        )
                        
                        # Khôi phục current_round nếu có
                        if 'current_round' in room_dict and room_dict['current_round']:
                            round_data = room_dict['current_round']
                            room.current_round = GameRound(
                                number=round_data['number'],
                                range_low=round_data['range_low'],
                                range_high=round_data['range_high'],
                                start_time=round_data['start_time'],
                                end_time=round_data['end_time']
                            )
                        
                        # Khôi phục scores
                        if 'scores' in room_dict:
                            room.scores = room_dict['scores']
                        
                        # Khôi phục round_number
                        if 'round_number' in room_dict:
                            room.round_number = room_dict['round_number']
                        
                        self.rooms[room_id] = room
                        logger.info(f"Loaded room: {room_id} - {room.name}")
                        
                    except Exception as e:
                        logger.error(f"Error loading room {room_id}: {e}")
                        continue
                
                logger.info(f"Successfully loaded {len(self.rooms)} rooms from file")
            else:
                logger.info("No persistence file found, starting with empty rooms")
                
        except Exception as e:
            logger.error(f"Error loading rooms from file: {e}")

    def start_cleanup_thread(self):
        """Khởi động thread dọn dẹp phòng không hoạt động"""
        def cleanup_inactive_rooms():
            while True:
                try:
                    current_time = time.time()
                    inactive_rooms = []

                    for room_id, room in self.rooms.items():
                        # Xóa phòng không có người chơi trong 5 phút
                        if len(room.players) == 0 and (current_time - room.created_at) > 300:
                            inactive_rooms.append(room_id)
                        # Xóa phòng không hoạt động trong 10 phút
                        elif not room.is_active and (current_time - room.created_at) > 600:
                            inactive_rooms.append(room_id)

                    for room_id in inactive_rooms:
                        self.delete_room(room_id)
                        logger.info(f"Cleaned up inactive room: {room_id}")

                    # Lưu rooms vào file sau mỗi lần cleanup
                    self.save_rooms_to_file()

                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")

                time.sleep(60)  # Chạy mỗi phút

    def normalize_room_id(self, room_id: str) -> str:
        """Chuẩn hóa room ID (chuyển về chữ thường)"""
        return room_id.lower().strip()

    def find_room_by_id(self, room_id: str) -> Optional[Room]:
        """Tìm phòng theo ID (không phân biệt chữ hoa/thường)"""
        normalized_id = self.normalize_room_id(room_id)

        # Tìm chính xác trước
        if room_id in self.rooms:
            return self.rooms[room_id]

        # Tìm theo ID đã chuẩn hóa
        for existing_id, room in self.rooms.items():
            if self.normalize_room_id(existing_id) == normalized_id:
                return room

        return None



    def create_room(self, room_id: str, room_name: str, max_players: int = 10,
                   password: str = None, is_private: bool = False) -> Optional[Room]:
        """Tạo phòng mới"""
        # Validation input
        if not room_id or not room_name:
            logger.warning("Create room failed: Empty room_id or room_name")
            return None
        
        if (len(room_id) < GAME_CONFIG['MIN_ROOM_ID_LENGTH'] or 
            len(room_id) > GAME_CONFIG['MAX_ROOM_ID_LENGTH']):
            logger.warning(f"Create room failed: Invalid room_id length: {len(room_id)}")
            return None
        
        if (len(room_name) < GAME_CONFIG['MIN_ROOM_NAME_LENGTH'] or 
            len(room_name) > GAME_CONFIG['MAX_ROOM_NAME_LENGTH']):
            logger.warning(f"Create room failed: Invalid room_name length: {len(room_name)}")
            return None
        
        # Kiểm tra ký tự đặc biệt trong room_id - cho phép chữ cái Unicode (bao gồm tiếng Việt)
        # Chỉ cho phép chữ cái, số, dấu cách, gạch dưới, gạch ngang và các ký tự Unicode
        import unicodedata
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -')
        for char in room_id:
            if char not in allowed_chars and not unicodedata.category(char).startswith('L'):
                logger.warning(f"Create room failed: Invalid characters in room_id: {room_id}")
                return None
        
        if len(self.rooms) >= GAME_CONFIG['MAX_ROOMS']:
            logger.warning("Create room failed: Max rooms reached")
            return None
        
        # Kiểm tra trùng lặp (không phân biệt chữ hoa/thường)
        normalized_id = self.normalize_room_id(room_id)
        for existing_id in self.rooms:
            if self.normalize_room_id(existing_id) == normalized_id:
                logger.warning(f"Create room failed: Room with similar ID already exists: {existing_id}")
                return None

        # Tạo round đầu tiên
        range_low, range_high = GAME_CONFIG['RANGE_DEFAULT']
        current_time = time.time()
        first_round = GameRound(
            number=random.randint(range_low, range_high),
            range_low=range_low,
            range_high=range_high,
            start_time=current_time,
            end_time=current_time + GAME_CONFIG['ROUND_TIME']
        )

        room = Room(
            id=room_id,
            name=room_name,
            created_at=current_time,
            current_round=first_round,
            players={},
            scores=defaultdict(int),
            round_number=1,
            is_active=True,
            max_players=max_players,
            password=password,
            is_private=is_private
        )

        self.rooms[room_id] = room
        logger.info(f"Created room: {room_id} ({room_name})")
        
        # Lưu rooms vào file sau khi tạo phòng
        self.save_rooms_to_file()
        
        return room

    def delete_room(self, room_id: str):
        """Xóa phòng"""
        room = self.find_room_by_id(room_id)
        if room:
            # Thông báo cho tất cả người chơi
            socketio.emit('room_deleted', {'room_id': room_id}, to=room_id)
            # Xóa khỏi quản lý
            del self.rooms[room.id]  # Sử dụng room.id gốc để xóa
            logger.info(f"Deleted room: {room_id}")

    def join_room(self, room_id: str, player_name: str, sid: str, password: str = None) -> Tuple[bool, str]:
        """Tham gia phòng"""
        # Validation input
        if not room_id or not player_name:
            logger.warning("Join room failed: Empty room_id or player_name")
            return False, "ID phòng và tên người chơi không được để trống"

        if (len(player_name) < GAME_CONFIG['MIN_PLAYER_NAME_LENGTH'] or
            len(player_name) > GAME_CONFIG['MAX_PLAYER_NAME_LENGTH']):
            logger.warning(f"Join room failed: Invalid player_name length: {len(player_name)}")
            return False, f"Tên người chơi phải từ {GAME_CONFIG['MIN_PLAYER_NAME_LENGTH']} đến {GAME_CONFIG['MAX_PLAYER_NAME_LENGTH']} ký tự"

        # Kiểm tra ký tự đặc biệt trong player_name - cho phép chữ cái Unicode (bao gồm tiếng Việt)
        import unicodedata
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -')
        for char in player_name:
            if char not in allowed_chars and not unicodedata.category(char).startswith('L'):
                logger.warning(f"Join room failed: Invalid characters in player_name: {player_name}")
                return False, "Tên người chơi chỉ được chứa chữ cái, số, dấu cách, gạch dưới và gạch ngang"

                # Tìm phòng (không phân biệt chữ hoa/thường)
        room = self.find_room_by_id(room_id)
        if not room:
            logger.warning(f"Join room failed: Room {room_id} not found")
            return False, "Phòng không tồn tại"

        # Kiểm tra mật khẩu
        if room.is_private and room.password != password:
            logger.warning(f"Join room failed: Wrong password for room {room_id}")
            return False, "Mật khẩu không đúng"

        # Kiểm tra số lượng người chơi
        if len(room.players) >= room.max_players:
            logger.warning(f"Join room failed: Room {room_id} is full")
            return False, "Phòng đã đầy"

        # Kiểm tra tên đã tồn tại
        if any(p.name == player_name for p in room.players.values()):
            logger.warning(f"Join room failed: Player name {player_name} already exists in room {room_id}")
            return False, "Tên người chơi đã tồn tại"

        # Tạo người chơi mới
        player = Player(
            name=player_name,
            sid=sid,
            joined_at=time.time(),
            last_guess_at=0
        )

        room.players[sid] = player
        self.player_rooms[sid] = room_id

        # Reset thời gian vòng chơi nếu vòng đã kết thúc
        current_time = time.time()
        if current_time > room.current_round.end_time:
            # Vòng đã kết thúc, tạo vòng mới
            self._start_new_round(room)
            logger.info(f"Round ended, started new round for new player {player_name}")

        logger.info(f"Player {player_name} joined room {room_id}")
        
        # Lưu rooms vào file sau khi có thay đổi
        self.save_rooms_to_file()
        
        return True, "Tham gia thành công"

    def leave_room(self, sid: str):
        """Rời phòng"""
        if sid not in self.player_rooms:
            return
        
        room_id = self.player_rooms[sid]
        room = self.find_room_by_id(room_id)
        if not room:
            return
        if sid in room.players:
            player_name = room.players[sid].name
            del room.players[sid]
            del self.player_rooms[sid]

            # Thông báo cho phòng
            socketio.emit('player_left', {
                'room_id': room_id,
                'player_name': player_name,
                'current_players': len(room.players)
            }, to=room_id)

            # Nếu phòng trống, đánh dấu không hoạt động
            if len(room.players) == 0:
                room.is_active = False

            # Lưu rooms vào file sau khi có thay đổi
            self.save_rooms_to_file()

            logger.info(f"Player {player_name} left room {room_id}")

    def make_guess(self, room_id: str, sid: str, guess: int) -> Tuple[bool, str, dict]:
        """Thực hiện đoán số"""
        # Validation input
        if not isinstance(guess, int):
            logger.warning(f"Make guess failed: Invalid guess type: {type(guess)}")
            return False, "Số đoán phải là số nguyên", {}

                # Tìm phòng (không phân biệt chữ hoa/thường)
        room = self.find_room_by_id(room_id)
        if not room or sid not in room.players:
            logger.warning(f"Make guess failed: Room {room_id} or player {sid} not found")
            return False, "Không tìm thấy phòng hoặc người chơi", {}
        player = room.players[sid]
        current_time = time.time()

        # Kiểm tra thời gian
        if current_time > room.current_round.end_time:
            logger.info(f"Round ended in room {room_id}, starting new round")
            # Tự động tạo vòng mới thay vì từ chối đoán
            self._start_new_round(room)
            # Cho phép đoán trong vòng mới
            return self.make_guess(room_id, sid, guess)

        # Kiểm tra rate limit và số lần đoán
        if not player.can_make_guess():
            if current_time - player.last_guess_at < GAME_CONFIG['RATE_LIMIT_MS'] / 1000:
                logger.warning(f"Make guess failed: Rate limit exceeded for player {player.name} in room {room_id}")
                return False, "Đoán quá nhanh, vui lòng chờ", {}
            else:
                logger.warning(f"Make guess failed: Max guesses per round exceeded for player {player.name} in room {room_id}")
                return False, f"Bạn đã đoán quá {GAME_CONFIG['MAX_GUESSES_PER_ROUND']} lần trong vòng này", {}

        # Kiểm tra phạm vi
        if guess < room.current_round.range_low or guess > room.current_round.range_high:
            logger.info(f"Make guess failed: Out of range guess {guess} in room {room_id}")
            return False, f"Số phải trong khoảng [{room.current_round.range_low}, {room.current_round.range_high}]", {}

        # Cập nhật thông tin người chơi
        player.last_guess_at = current_time
        player.total_guesses += 1
        player.guesses_this_round += 1

        # Kiểm tra kết quả
        if guess == room.current_round.number:
            # Đoán đúng
            time_bonus = max(0, int((room.current_round.end_time - current_time) / 10))
            base_score = GAME_CONFIG['SCORE_CORRECT']
            streak_bonus = int(player.streak * GAME_CONFIG['SCORE_STREAK_MULTIPLIER'])
            total_score = base_score + time_bonus + streak_bonus

            player.score += total_score
            player.correct_guesses += 1
            player.streak += 1

            room.scores[player.name] = player.score
            room.current_round.winner = player.name
            room.current_round.total_guesses += 1

            # Lưu lịch sử vòng
            round_history = {
                'round_number': room.round_number,
                'number': room.current_round.number,
                'winner': player.name,
                'total_guesses': room.current_round.total_guesses,
                'duration': current_time - room.current_round.start_time
            }
            room.game_history.append(round_history)

            # Lưu số đã đoán đúng trước khi tạo vòng mới
            correct_number = room.current_round.number

            # Tạo vòng mới
            self._start_new_round(room)
            
            # Lưu rooms vào file sau khi có thay đổi điểm số
            self.save_rooms_to_file()

            return True, f"🎉 Chính xác! Số cần tìm là {correct_number}", {
                'correct': True,
                'score_gained': total_score,
                'new_total_score': player.score,
                'streak': player.streak,
                'time_bonus': time_bonus,
                'streak_bonus': streak_bonus,
                'total_guesses': room.current_round.total_guesses
            }
        else:
            # Đoán sai
            player.streak = 0
            room.current_round.total_guesses += 1

            # Gợi ý rõ ràng hơn cho người chơi
            if guess < room.current_round.number:
                hint = f"Số cần tìm lớn hơn {guess}"
            else:
                hint = f"Số cần tìm nhỏ hơn {guess}"
                
            # Lưu rooms vào file sau khi có thay đổi thống kê
            self.save_rooms_to_file()
            
            return True, hint, {
                'correct': False,
                'hint': hint,
                'range': [room.current_round.range_low, room.current_round.range_high],
                'total_guesses': room.current_round.total_guesses
            }

    def _start_new_round(self, room: Room, reset_mode: bool = False):
        """Bắt đầu vòng mới"""
        if reset_mode:
            room.round_number = 1
        elif room.round_number == 0:  # Nếu chưa có vòng nào
            room.round_number = 1
        else:
            room.round_number += 1

        # Reset guesses_this_round cho tất cả người chơi
        for player in room.players.values():
            player.guesses_this_round = 0

        range_low, range_high = GAME_CONFIG['RANGE_DEFAULT']
        current_time = time.time()

        new_round = GameRound(
            number=random.randint(range_low, range_high),
            range_low=range_low,
            range_high=range_high,
            start_time=current_time,
            end_time=current_time + GAME_CONFIG['ROUND_TIME']
        )

        room.current_round = new_round

        # Thông báo vòng mới
        socketio.emit('new_round', {
            'room_id': room.id,
            'round_number': room.round_number,
            'range': [range_low, range_high],
            'end_time': new_round.end_time,
            'previous_winner': room.current_round.winner,
            'message': f"🎮 Vòng {room.round_number}: Đoán số từ {range_low} đến {range_high}"
        }, to=room.id)

        # Emit event cũ để tương thích ngược
        emit_legacy_events(room.id, 'round', {
            'round_number': room.round_number,
            'range': [range_low, range_high],
            'end_time': new_round.end_time
        })

        logger.info(f"Started new round {room.round_number} in room {room.id}")
        
        # Lưu rooms vào file sau khi có thay đổi
        self.save_rooms_to_file()

    def reset_room(self, room_id: str, admin_sid: str) -> Tuple[bool, str]:
        """Reset phòng (chỉ admin)"""
        room = self.find_room_by_id(room_id)
        if not room:
            return False, "Phòng không tồn tại"
        if admin_sid not in room.players:
            return False, "Bạn không phải người chơi trong phòng này"

        # Reset điểm số
        for player in room.players.values():
            player.score = 0
            player.streak = 0
            player.total_guesses = 0
            player.correct_guesses = 0

        room.scores.clear()
        room.game_history.clear()

        # Tạo vòng mới (sẽ set round_number = 1)
        self._start_new_round(room, reset_mode=True)

        logger.info(f"Room {room_id} reset by admin")
        
        # Lưu rooms vào file sau khi có thay đổi
        self.save_rooms_to_file()
        
        return True, "Reset phòng thành công"

    def get_room_info(self, room_id: str) -> Optional[dict]:
        """Lấy thông tin phòng"""
        room = self.find_room_by_id(room_id)
        if not room:
            return None
        return {
            'id': room.id,
            'name': room.name,
            'round_number': room.round_number,
            'current_round': {
                'range': [room.current_round.range_low, room.current_round.range_high],
                'end_time': room.current_round.end_time,
                'total_guesses': room.current_round.total_guesses
            },
            'players': [
                {
                    'name': p.name,
                    'score': p.score,
                    'streak': p.streak,
                    'correct_guesses': p.correct_guesses
                } for p in room.players.values()
            ],
            'scores': dict(room.scores),
            'is_private': room.is_private,
            'max_players': room.max_players,
            'current_players': len(room.players)
        }

    def get_available_rooms(self) -> List[dict]:
        """Lấy danh sách phòng có sẵn"""
        available_rooms = []
        for room in self.rooms.values():
            if not room.is_private and room.is_active:
                available_rooms.append({
                    'id': room.id,
                    'name': room.name,
                    'current_players': len(room.players),
                    'max_players': room.max_players,
                    'round_number': room.round_number
                })
        return available_rooms

# ---- Helper functions
def emit_legacy_events(room_id, event_type, data, target_sid=None):
    """Emit các events cũ để tương thích ngược"""
    try:
        if event_type == 'round':
            # Emit event 'round' cũ
            socketio.emit('round', {
                'room': room_id,
                'round': data.get('round_number', '?'),
                'range': data.get('range', [1, 100]),
                'endsAt': data.get('end_time', 0) * 1000  # Convert to milliseconds
            }, to=room_id)

        elif event_type == 'scoreboard':
            # Emit event 'scoreboard' cũ
            socketio.emit('scoreboard', data.get('scores', {}), to=room_id)

        elif event_type == 'message':
            # Emit event 'message' cũ - chỉ cho người chơi cụ thể nếu có target_sid
            if target_sid:
                socketio.emit('message', {
                    'room': room_id,
                    'msg': data.get('message', '')
                }, to=target_sid)
            else:
                socketio.emit('message', {
                    'room': room_id,
                    'msg': data.get('message', '')
                }, to=room_id)

    except Exception as e:
        logger.error(f"Error emitting legacy events: {e}")

# Khởi tạo game manager
game_manager = GameManager()

# Tự động tạo phòng lobby mặc định
def create_default_rooms():
    """Tạo các phòng mặc định khi server khởi động"""
    try:
        # Tạo phòng lobby nếu chưa có
        if "lobby" not in game_manager.rooms:
            lobby_room = game_manager.create_room("lobby", "Phòng Lobby", 20)
            if lobby_room:
                logger.info("✅ Tạo phòng lobby mặc định thành công")
            else:
                logger.warning("❌ Không thể tạo phòng lobby mặc định")

        # Tạo phòng demo nếu chưa có
        if "demo" not in game_manager.rooms:
            demo_room = game_manager.create_room("demo", "Phòng Demo", 10)
            if demo_room:
                logger.info("✅ Tạo phòng demo thành công")
            else:
                logger.warning("❌ Không thể tạo phòng demo")

    except Exception as e:
        logger.error(f"Lỗi khi tạo phòng mặc định: {e}")

# Tạo phòng mặc định
create_default_rooms()

# Routes
@app.route("/")
def home():
    return jsonify({
        "message": "Guess Number Server v2.0",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/rooms")
def get_rooms():
    """API lấy danh sách phòng"""
    return jsonify({
        "rooms": game_manager.get_available_rooms(),
        "total": len(game_manager.rooms)
    })

@app.route("/api/rooms/<room_id>")
def get_room_info(room_id):
    """API lấy thông tin phòng"""
    room_info = game_manager.get_room_info(room_id)
    if room_info:
        return jsonify(room_info)
    return jsonify({"error": "Phòng không tồn tại"}), 404

@app.route("/api/rooms", methods=["POST"])
def create_room_api():
    """API tạo phòng"""
    data = request.get_json()
    room_id = data.get('room_id', '').strip()
    room_name = data.get('room_name', 'Phòng mới').strip()
    max_players = min(data.get('max_players', 10), GAME_CONFIG['MAX_PLAYERS_PER_ROOM'])
    password = data.get('password', '').strip() or None
    is_private = bool(password)

    if not room_id:
        return jsonify({"error": "ID phòng không được để trống"}), 400

    room = game_manager.create_room(room_id, room_name, max_players, password, is_private)
    if room:
        return jsonify({
            "success": True,
            "room": game_manager.get_room_info(room_id)
        })
    else:
        return jsonify({"error": "Không thể tạo phòng"}), 400

# Socket.IO Events
@socketio.on('create_room')
def on_create_room(data):
    """Tạo phòng mới"""
    room_id = data.get('room_id', '').strip()
    room_name = data.get('room_name', '').strip()
    max_players = data.get('max_players', 10)

    if not room_id or not room_name:
        emit('create_room_error', {'error': 'ID phòng và tên phòng không được để trống'})
        return

    # Tạo phòng
    room = game_manager.create_room(room_id, room_name, max_players)

    if room:
        # Tham gia Socket.IO room ngay sau khi tạo
        join_room(room_id)

        emit('room_created', {
            'room_id': room_id,
            'room_name': room_name,
            'max_players': max_players
        })

        logger.info(f"Room {room_id} created successfully")
        
        # Lưu rooms vào file sau khi tạo phòng
        game_manager.save_rooms_to_file()
    else:
        emit('create_room_error', {'error': 'Không thể tạo phòng'})
        logger.warning(f"Failed to create room {room_id}")

@socketio.on('connect')
def on_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'sid': request.sid})

@socketio.on('disconnect')
def on_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    game_manager.leave_room(request.sid)
    
    # Lưu rooms vào file sau khi disconnect
    game_manager.save_rooms_to_file()

@socketio.on('join_room')
def on_join_room(data):
    """Tham gia phòng"""
    room_id = data.get('room_id', '').strip()
    player_name = data.get('player_name', 'Player').strip()[:20]

    # Xử lý password an toàn
    password_raw = data.get('password')
    if password_raw is None:
        password = None
    else:
        password = password_raw.strip() or None

    if not room_id:
        emit('join_error', {'error': 'ID phòng không được để trống'})
        return

    success, message = game_manager.join_room(room_id, player_name, request.sid, password)
    
    if success:
        room = game_manager.find_room_by_id(room_id)
        # Tham gia Socket.IO room để nhận tin nhắn
        join_room(room_id)
        logger.info(f"Player {player_name} joined Socket.IO room {room_id}")

        # Gửi thông tin phòng
        emit('room_joined', {
            'room_id': room_id,
            'room_name': room.name,
            'player_name': player_name,
            'room_info': game_manager.get_room_info(room_id)
        })

        # Thông báo cho phòng
        socketio.emit('player_joined', {
            'room_id': room_id,
            'player_name': player_name,
            'current_players': len(room.players)
        }, to=room_id)

        # Nếu đây là người chơi đầu tiên, bắt đầu vòng 1
        if len(room.players) == 1:
            # Không cần gọi _start_new_round vì phòng đã có vòng 1 sẵn
            logger.info(f"First player joined room {room_id}, room already has round 1 ready")

        logger.info(f"Player {player_name} successfully joined room {room_id}")
        
        # Lưu rooms vào file sau khi tham gia phòng
        game_manager.save_rooms_to_file()
    else:
        emit('join_error', {'error': message})
        logger.warning(f"Failed to join room: {message}")

@socketio.on('join')
def on_join_legacy(data):
    """Event handler cũ để tương thích ngược - chuyển đổi sang join_room"""
    logger.info(f"Legacy 'join' event received, converting to 'join_room'")

    # Chuyển đổi data format cũ sang mới
    room_id = data.get('room', '').strip()
    player_name = data.get('name', 'Player').strip()[:20]

    if not room_id:
        emit('join_error', {'error': 'ID phòng không được để trống'})
        return

    # Gọi lại event handler mới
    on_join_room({
        'room_id': room_id,
        'player_name': player_name,
        'password': None
    })

@socketio.on('leave_room')
def on_leave_room():
    """Rời phòng"""
    game_manager.leave_room(request.sid)
    
    # Lưu rooms vào file sau khi rời phòng
    game_manager.save_rooms_to_file()
    
    emit('room_left', {'message': 'Đã rời phòng'})

@socketio.on('make_guess')
def on_make_guess(data):
    """Đoán số"""
    room_id = data.get('room_id', '').strip()
    try:
        guess = int(data.get('guess'))
    except (ValueError, TypeError):
        emit('guess_error', {'error': 'Số không hợp lệ'})
        return

    success, message, details = game_manager.make_guess(room_id, request.sid, guess)

    if success:
        emit('guess_result', {
            'message': message,
            'details': details
        })

        # Emit event cũ để tương thích ngược - chỉ cho người chơi đã đoán
        emit_legacy_events(room_id, 'message', {
            'message': message
        }, target_sid=request.sid)

        # Cập nhật bảng điểm nếu đoán đúng
        if details.get('correct'):
            socketio.emit('scoreboard_updated', {
                'scores': game_manager.get_room_info(room_id)['scores']
            }, to=room_id)
            
            # Lưu rooms vào file sau khi có thay đổi điểm số
            game_manager.save_rooms_to_file()
    else:
        emit('guess_error', {'error': message})

@socketio.on('guess')
def on_guess_legacy(data):
    """Event handler cũ để tương thích ngược - chuyển đổi sang make_guess"""
    logger.info(f"Legacy 'guess' event received, converting to 'make_guess'")

    # Chuyển đổi data format cũ sang mới
    room_id = data.get('room', '').strip()
    try:
        guess = int(data.get('number'))
    except (ValueError, TypeError):
        emit('guess_error', {'error': 'Số không hợp lệ'})
        return

    # Gọi lại event handler mới
    on_make_guess({
        'room_id': room_id,
        'guess': guess
    })

@socketio.on('chat_message')
def on_chat_message(data):
    """Gửi tin nhắn chat"""
    room_id = data.get('room_id', '').strip()
    message = data.get('message', '').strip()

    # Validation input
    if not room_id or not message:
        emit('chat_error', {'error': 'ID phòng và tin nhắn không được để trống'})
        return

    if len(message) > GAME_CONFIG['MAX_CHAT_LENGTH']:
        emit('chat_error', {'error': f'Tin nhắn quá dài (tối đa {GAME_CONFIG["MAX_CHAT_LENGTH"]} ký tự)'})
        return

                # Tìm phòng (không phân biệt chữ hoa/thường)
    room = game_manager.find_room_by_id(room_id)
    if not room:
        logger.warning(f"Chat failed: Room {room_id} not found")
        emit('chat_error', {'error': 'Không thể gửi tin nhắn'})
        return
    
    if request.sid not in room.players:
        logger.warning(f"Chat failed: Player {request.sid} not found in room {room_id}")
        emit('chat_error', {'error': 'Không thể gửi tin nhắn'})
        return
    
    player = room.players[request.sid]

    # Thêm tin nhắn chat mới
    player.add_chat_message()

    chat_data = {
        'room_id': room_id,
        'player_name': player.name,
        'message': message,
        'timestamp': time.time(),
        'type': 'chat'
    }

    socketio.emit('chat_message', chat_data, to=room_id)
    
    # Lưu rooms vào file sau khi có thay đổi
    game_manager.save_rooms_to_file()
    
    logger.info(f"Chat in room {room_id}: {player.name}: {message}")

@socketio.on('chat')
def on_chat_legacy(data):
    """Event handler cũ để tương thích ngược - chuyển đổi sang chat_message"""
    logger.info(f"Legacy 'chat' event received, converting to 'chat_message'")

    # Chuyển đổi data format cũ sang mới
    room_id = data.get('room', '').strip()
    message = data.get('text', '').strip()

    # Gọi lại event handler mới
    on_chat_message({
        'room_id': room_id,
        'message': message
    })

@socketio.on('reset_room')
def on_reset_room(data):
    """Reset phòng"""
    room_id = data.get('room_id', '').strip()

    success, message = game_manager.reset_room(room_id, request.sid)

    if success:
        emit('room_reset', {'message': message})
        socketio.emit('room_reset', {'message': message}, to=room_id)
        
        # Lưu rooms vào file sau khi reset phòng
        game_manager.save_rooms_to_file()
        
        logger.info(f"Room {room_id} reset successfully")
    else:
        emit('reset_error', {'error': message})

@socketio.on('get_room_info')
def on_get_room_info(data):
    """Lấy thông tin phòng"""
    room_id = data.get('room_id', '').strip()
    room_info = game_manager.get_room_info(room_id)

    if room_info:
        emit('room_info', room_info)
    else:
        emit('room_info_error', {'error': 'Phòng không tồn tại'})

@socketio.on('get_available_rooms')
def on_get_available_rooms():
    """Lấy danh sách phòng có sẵn"""
    rooms = game_manager.get_available_rooms()
    emit('available_rooms', {'rooms': rooms})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    logger.info("Starting Guess Number Server v2.0...")
    logger.info(f"Game config: {GAME_CONFIG}")

    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
