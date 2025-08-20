# 🎮 Guess Number Web - Daily Push Plan

## Day 1
- Minimal server (`server/server.py`) + minimal client (`client/index.html`).
- Features: join, guess, LOW/HIGH/CORRECT, next round.

## Day 2
- Add scoreboard + nicer layout.
- Files: `client/style.css`, `client/game.js`, server scores broadcast.

## Day 3
- Rooms (`?room=abc`), timer per round, basic rate limit, chat.
- Files updated: `server/server.py`, `client/*`.

## Day 4
- Docker + docker-compose + README.
- Run:
  ```bash
  cd docker
  docker compose up --build
  ```
- Open client at http://localhost:8080 (server at :5000).
