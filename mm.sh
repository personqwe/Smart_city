#!/bin/bash

function stop_processes() {
    echo "Stopping Radio.py and MagicMirror..."
    pkill -f "python3 Radio.py"
    pkill -f "electron --no-sandbox --disable-gpu js/electron.js"
    exit
}

# MagicMirror 실행
cd ~/MagicMirror
DISPLAY="${DISPLAY:=:0}" ./node_modules/.bin/electron --no-sandbox --disable-gpu js/electron.js &

sleep 5

# Radio.py 실행
cd /root/MagicMirror/installers/  # Change this to the directory containing Radio.py
python3 Radio.py &

# 종료 함수를 호출하는 부분
trap stop_processes SIGINT

echo "Press Ctrl+C to stop Radio.py and MagicMirror"
while true; do
    sleep 1
done