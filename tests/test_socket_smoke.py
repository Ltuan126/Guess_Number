import time, random, sys, socketio
SERVER = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:5000"
ROOM   = sys.argv[2] if len(sys.argv)>2 else "test1"
NAME   = sys.argv[3] if len(sys.argv)>3 else f"Tester{random.randint(100,999)}"

sio = socketio.Client(logger=True, engineio_logger=False)

@sio.event
def connect():
    print("[connect] ok"); sio.emit("join", {"room": ROOM, "name": NAME})

@sio.on("round")
def on_round(d):
    print("[round]", d)
    lo, hi = d.get("range",[1,100])
    for _ in range(5):
        g = random.randint(lo,hi)
        print("[guess]", g); sio.emit("guess", {"room":ROOM,"name":NAME,"number":g})
        time.sleep(0.55)   # >= 500ms để không dính rate-limit

@sio.on("result")
def on_result(d): print("[result]", d)

@sio.on("message")
def on_message(d): print("[message]", d)

@sio.on("scoreboard")
def on_scores(d): print("[scores]", d)

@sio.on("error")
def on_error(d): print("[error]", d)

if __name__=="__main__":
    sio.connect(SERVER, transports=["websocket"])
    sio.sleep(10)   # đủ dài để thấy 1 vòng đoán
    sio.disconnect()
