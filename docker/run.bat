@echo off
cd /d %~dp0
docker compose up -d --build

echo.
echo ✅ Guess Number da chay!
echo    UI:     http://localhost:8080
echo    Server: http://localhost:5000
