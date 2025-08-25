# 🎮 Guess Number – Multiplayer Game (Flask + Socket.IO + Vanilla JS)

## 📌 Giới thiệu

Dự án **Guess Number** là một ứng dụng web nhiều người chơi hoàn chỉnh. Người chơi có thể tạo phòng mới hoặc tham gia phòng có sẵn, đoán số bí mật trong khoảng cho trước. Hệ thống ghi nhận điểm, hiển thị bảng xếp hạng, cho phép chat trong phòng và tự động reset vòng chơi.

## 🚀 Tính năng chính

### 🔐 Quản lý phòng
- **Tạo phòng mới**: Tự động tạo mã phòng 6 ký tự ngẫu nhiên
- **Tham gia phòng**: Nhập mã phòng có sẵn để tham gia
- **Danh sách phòng**: Xem và tham gia các phòng đang hoạt động
- **Copy mã phòng**: Chia sẻ mã phòng dễ dàng với bạn bè
- **Rời phòng**: Quay lại màn hình chính bất cứ lúc nào

### 🎯 Gameplay
- Đoán số với phản hồi **LOW/HIGH/ĐÚNG** theo thời gian thực
- Hiển thị thông tin vòng chơi chi tiết (số vòng, khoảng số)
- Bảng xếp hạng cập nhật tức thì
- Chat trong phòng với tất cả người chơi
- Khôi phục trạng thái game khi refresh trang

### 💻 Giao diện & UX
- Giao diện responsive, thân thiện với người dùng
- Status messages rõ ràng cho mọi hành động
- Keyboard shortcuts (Enter để submit, Tab để navigate)
- Auto-focus và validation input thông minh
- Hiệu ứng visual feedback khi thực hiện hành động

## 🛠️ Công nghệ sử dụng

- **Backend**: [Flask](https://flask.palletsprojects.com/) + [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- **Frontend**: HTML, CSS, JavaScript (Vanilla + Socket.IO client)
- **Triển khai**: Docker, docker-compose, Nginx (serve client)
- **Test**: Python unittest/pytest + script test client (socket)

## 📂 Cấu trúc thư mục

guess-number-web-final/
│
├── client/ # Giao diện web (HTML, CSS, JS)
│ ├── index.html
│ ├── style.css
│ └── game.js
│
├── server/ # Backend Flask-SocketIO
│ ├── server.py
│ ├── requirements.txt
│ └── tests/ # Unit tests (sẽ bổ sung)
│
├── docker/ # Dockerfile + docker-compose
│ ├── Dockerfile
│ └── docker-compose.yml
│
├── docs/ # Tài liệu, demo script, báo cáo
│
└── README.md # Giới thiệu & hướng dẫn

r
Sao chép
Chỉnh sửa

## ▶️ Cách chạy

### Cách 1: Chạy bằng Python (local)

Yêu cầu: Python >= 3.11, pip

```bash
cd server
pip install -r requirements.txt
python server.py
Mở client/index.html trực tiếp trong trình duyệt.

Server lắng nghe tại http://localhost:5000.

Cách 2: Chạy bằng Docker Compose
Yêu cầu: Docker, docker-compose

bash
Sao chép
Chỉnh sửa
cd docker
docker compose up --build
Frontend: http://localhost:8080

Backend (API/Socket.IO): http://localhost:5000

👥 Phân công nhóm
Phương (Backend): phát triển và hoàn thiện server.py, validation, rate-limit, unit test.

Hùng (Frontend UI): thiết kế giao diện index.html + style.css, scoreboard, timer, trạng thái kết nối.

Tuấn (Frontend JS + DevOps): refactor game.js, xử lý reconnect, viết Dockerfile, docker-compose, script chạy nhanh, README.

Thành (Kiểm thử & Demo): viết script test socket, test multi-user, sửa bug nhỏ, chuẩn bị demo và slide.

🧪 Test
Chạy test backend:

bash
Sao chép
Chỉnh sửa
cd server
pytest
Script test client (giả lập nhiều user): tools/test_client.py (sẽ bổ sung).

📸 Demo
Người chơi nhập tên và tham gia phòng → mỗi người có scoreboard riêng.

Giao diện hiển thị timer, thông báo kết quả đoán (LOW/HIGH/ĐÚNG).

Chat realtime trong phòng.

Khi có người đoán đúng → server broadcast thông báo và bắt đầu vòng mới.

✨ Dự án Guess Number là sản phẩm học tập phục vụ môn Lập trình mạng.
Nhóm mong muốn cải thiện kỹ năng teamwork, Git workflow, và triển khai ứng dụng thực tế.
```
