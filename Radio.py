import os
import socketio
import time
import threading

# 소켓 클라이언트 생성
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to server')

@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from server')

# GPIO 핀 번호 설정
button_pin = 90  # 버튼의 GPIO 핀 번호

# GPIO 핀 모드 설정
def setup_gpio(pin):
    os.system(f"echo {pin} > /sys/class/gpio/export")
    os.system(f"echo in > /sys/class/gpio/gpio{pin}/direction")

# 버튼 상태를 읽는 함수
def read_button_state(pin):
    with open(f"/sys/class/gpio/gpio{pin}/value", "r") as file:
        return int(file.read())

# 버튼을 눌렀을 때 실행할 함수
def Play_Radio():
    sio.emit('radio', 'play_radio')
    print('Button pressed! Sending play_radio')

def Stop_Radio():
    sio.emit('radio', 'stop_radio')
    print('Button pressed again! Sending stop_radio')

# GPIO 설정 및 버튼 이벤트 처리
def setup_and_poll_button(pin):
    setup_gpio(pin)
    prev_button_state = 0
    button_press_count = 0  # 버튼 눌림 횟수
    while True:
        button_state = read_button_state(pin)
        if button_state == 1 and prev_button_state == 0:  # 버튼이 눌렸을 때
            button_press_count += 1
            if button_press_count == 1:
                Play_Radio()
            elif button_press_count == 2:
                Stop_Radio()
                button_press_count = 0  # 초기화
        prev_button_state = button_state
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        button_thread = threading.Thread(target=setup_and_poll_button, args=(button_pin,))
        button_thread.start()

        sio.connect('http://192.168.9.115:3000')  # 서버 IP 주소로 변경

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        sio.disconnect()
        os.system(f"echo {button_pin} > /sys/class/gpio/unexport")
