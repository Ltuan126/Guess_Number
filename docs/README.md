# 🎮 Guess Number – Multiplayer Game (Flask + Socket.IO + Vanilla JS)

# <<<<<<< HEAD

## 📌 Giới thiệu

Dự án **Guess Number** là một ứng dụng web nhiều người chơi. Người chơi tham gia vào phòng, nhập tên và dự đoán số bí mật trong khoảng cho trước. Hệ thống ghi nhận điểm, hiển thị bảng xếp hạng, cho phép chat trong phòng và tự động reset vòng chơi sau khi có người đoán đúng hoặc hết thời gian.

## 🚀 Tính năng chính

- Đăng nhập nhanh bằng tên, tham gia phòng (room).
- Đoán số với phản hồi **LOW/HIGH/ĐÚNG** theo thời gian thực.
- Bộ đếm ngược cho mỗi vòng chơi (30 giây).
- Bảng xếp hạng (scoreboard) cập nhật tức thì.
- Chat trong phòng với tất cả người chơi.
- Tích hợp **Docker Compose** để chạy client + server trong 1 lệnh.

## 🛠️ Công nghệ sử dụng

- **Backend**: [Flask](https://flask.palletsprojects.com/) + [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- **Frontend**: HTML, CSS, JavaScript (Vanilla + Socket.IO client)
- **Triển khai**: Docker, docker-compose, Nginx (serve client)
- **Test**: Python unittest/pytest + script test client (socket)

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
