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
button_pin2 = 65
musicFolder = '/root/MagicMirror/Music/'  # 음악 파일 경로
musicFiles = []  # 음악 파일 리스트를 저장할 리스트 변수

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
    print('Button pressed! Sending stop_radio')

def Play_Music():
    sio.emit('Play_Music', 'Play_Music')
    print('Button pressed! Sending Play_Music')

def Next_Music():
    sio.emit('Next_Music', 'Next_Music')
    print('Button pressed! Sending Play_Music')

def Start_Car():
    sio.emit('Car_State', 'start')
    print('Button pressed! Starting Car')

def Stop_Car():
    sio.emit('Car_State', 'stop')
    print('Button pressed! Stoping Car')


def File_Load():
    global musicFiles  # musicFiles 변수를 함수 내에서 수정 가능하도록 global 선언
    try:
        files = os.listdir(musicFolder)
        musicFiles = [file for file in files if file.endswith('.mp3')]
        print('파일 불러옴', musicFiles)
        if len(musicFiles) == 0:
            print('디렉토리에서 음악 파일을 찾을 수 없습니다.')
            return
    except Exception as err:
        print(f'디렉토리 읽기 오류: {err}')

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
                Play_Music()
            elif button_press_count < len(musicFiles) + 2:
                Next_Music()
            elif button_press_count == len(musicFiles) + 2:
                Stop_Radio()
                button_press_count = 0  # 초기화
        prev_button_state = button_state
        time.sleep(0.1)

def setup_and_poll_button2(pin):
    setup_gpio(pin)
    prev_button_state = 0
    button_press_count = 0  # 버튼 눌림 횟수
    while True:
        button_state = read_button_state(pin)
        if button_state == 1 and prev_button_state == 0:  # 버튼이 눌렸을 때
            button_press_count += 1
            if button_press_count == 1:
                Start_Car()
            elif button_press_count == 2:
                Stop_Car()
                button_press_count = 0  # 초기화
        prev_button_state = button_state
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        File_Load()  # 음악 파일 불러오기
        num_music_files = len(musicFiles)  # 음악 파일 갯수 저장
        button_thread = threading.Thread(target=setup_and_poll_button, args=(button_pin,))
        button_thread.start()
        button_thread2 = threading.Thread(target=setup_and_poll_button2, args=(button_pin2,))
        button_thread2.start()

        sio.connect('http://192.168.9.115:3000')  # 서버 IP 주소로 변경

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        sio.disconnect()
        os.system(f"echo {button_pin} > /sys/class/gpio/unexport")