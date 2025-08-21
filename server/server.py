from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room
from collections import defaultdict
import random, time, os

# import hàm chọn gợi ý
from Mathematical_logic.scheduler import choose_hint_for_round

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

ROUND_TIME = int(os.getenv("ROUND_TIME", 30))
def now_ms(): return int(time.time() * 1000)

def range_for_round(rnum: int):
    if rnum <= 1: return 1, 10
    blk = (rnum - 2) // 3
    return 10, 100 + 100 * blk

rooms = {}

def ensure_room(room: str):
    if room not in rooms:
        lo, hi = range_for_round(1)
        rooms[room] = dict(
            round=1, lo=lo, hi=hi,
            secret=random.randint(lo, hi),
            scores=defaultdict(int),
            endsAt=now_ms() + ROUND_TIME * 1000,
            lastGuessTs=defaultdict(lambda: 0),
            hints=[],
            hint_text=""
        )

def new_round(room: str):
    r = rooms[room]
    r["round"] += 1
    r["lo"], r["hi"] = range_for_round(r["round"])
    r["secret"] = random.randint(r["lo"], r["hi"])
    r["endsAt"] = now_ms() + ROUND_TIME * 1000

    # chỉ từ round 2 mới có gợi ý
    hint_text, tag = choose_hint_for_round(r["round"], r["secret"], r["hints"])
    r["hint_text"] = hint_text if tag != "none" else ""
    if tag != "none": r["hints"].append(tag)

    payload = {
        "room": room,
        "round": r["round"],
        "range": [r["lo"], r["hi"]],
        "endsAt": r["endsAt"],
    }
    if r["hint_text"]:
        payload["hint"] = r["hint_text"]

    socketio.emit("round", payload, to=room)

@app.route("/")
def home():
    return "Guess Number Server Running!"

@socketio.on("join")
def on_join(data):
    room = (data.get("room") or "lobby").strip()[:24]
    name = (data.get("name") or "Player").strip()[:20]
    ensure_room(room)
    join_room(room)
    emit("message", {"room": room, "msg": f"{name} đã tham gia phòng {room}"}, to=room)
    r = rooms[room]
    payload = {
        "room": room,
        "round": r["round"],
        "range": [r["lo"], r["hi"]],
        "endsAt": r["endsAt"]
    }
    if r.get("hint_text"):
        payload["hint"] = r["hint_text"]
    emit("round", payload)
    emit("scoreboard", {"room": room, "scores": r["scores"]})

@socketio.on("guess")
def on_guess(data):
    room = (data.get("room") or "lobby").strip()[:24]
    name = (data.get("name") or "Player").strip()[:20]
    try:
        g = int(data.get("number"))
    except:
        emit("result", {"msg": "INVALID"}); return

    ensure_room(room); r = rooms[room]
    if now_ms() > r["endsAt"]:
        socketio.emit("message", {"room": room, "msg": f"Hết giờ! Số đúng là {r['secret']}."}, to=room)
        new_round(room)

    sid = request.sid
    last = r["lastGuessTs"][sid]
    if now_ms() - last < 500:
        emit("error", {"code":"RATE_LIMIT","msg":"Đoán hơi nhanh, thử lại sau."})
        return
    r["lastGuessTs"][sid] = now_ms()

    if g < r["lo"] or g > r["hi"]:
        emit("result", {"msg": f"OUT_OF_RANGE [{r['lo']},{r['hi']}]"}) ; return

    if g < r["secret"]:
        emit("result", {"msg": "LOW"})
    elif g > r["secret"]:
        emit("result", {"msg": "HIGH"})
    else:
        r["scores"][name] += 1
        socketio.emit("message", {"room": room, "msg": f"🎉 {name} đoán đúng số {r['secret']}!"}, to=room)
        socketio.emit("scoreboard", {"room": room, "scores": r["scores"]}, to=room)
        new_round(room)

@socketio.on("chat")
def on_chat(data):
    room = (data.get("room") or "lobby").strip()[:24]
    name = (data.get("name") or "Player").strip()[:20]
    text = (data.get("text") or "")[:200]
    socketio.emit("chat", {"room": room, "name": name, "text": text, "ts": int(time.time())}, to=room)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
