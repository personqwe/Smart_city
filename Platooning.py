import socketio
import sys
import os

# GPIO pin 상수 정의
GPIO_PIN1 = 89  # Right side motor pin cw
GPIO_PIN2 = 90  # Right side motor pin ccw
GPIO_PIN3 = 65  # Left side motor pin cw
GPIO_PIN4 = 66  # Left side motor pin ccw

sio = socketio.Client()

@sio.event
def connect():
    print('서버에 연결되었습니다.')

@sio.event
def disconnect():
    print('서버와 연결이 끊어졌습니다.')

@sio.on('start')  # 'start' 이벤트 수신
def receive_start_data(data):
    print("Received start data:", data)
    process_received_data(data)

def process_received_data(data):
    try:
        if data == 'L':
            set_motor_speed(1, 0, 0, 1)
        elif data == 'R':
            set_motor_speed(0, 1, 1, 0)
        elif data == 'F':
            set_motor_speed(1, 0, 1, 0)
        elif data == 'S':
            set_motor_speed(0, 0, 0, 0)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping motors.")
        set_motor_speed(0, 0, 0, 0)

def set_motor_speed(speed1, speed2, speed3, speed4):
    with open(f"/sys/class/gpio/gpio{GPIO_PIN1}/value", "w") as file1:
        file1.write(str(speed1))

    with open(f"/sys/class/gpio/gpio{GPIO_PIN2}/value", "w") as file2:
        file2.write(str(speed2))

    with open(f"/sys/class/gpio/gpio{GPIO_PIN3}/value", "w") as file3:
        file3.write(str(speed3))

    with open(f"/sys/class/gpio/gpio{GPIO_PIN4}/value", "w") as file4:
        file4.write(str(speed4))

def export_gpio(gpio_num):
    with open("/sys/class/gpio/export", "w") as file:
        file.write(str(gpio_num))

def set_gpio_direction(gpio_num, direction):
    with open(f"/sys/class/gpio/gpio{gpio_num}/direction", "w") as file:
        file.write(direction)

def unexport_gpio(gpio_num):
    with open("/sys/class/gpio/unexport", "w") as file:
        file.write(str(gpio_num))

# GPIO 초기화 및 설정
export_gpio(GPIO_PIN1)
export_gpio(GPIO_PIN2)
export_gpio(GPIO_PIN3)
export_gpio(GPIO_PIN4)

set_gpio_direction(GPIO_PIN1, "out")
set_gpio_direction(GPIO_PIN2, "out")
set_gpio_direction(GPIO_PIN3, "out")
set_gpio_direction(GPIO_PIN4, "out")

try:
    # 데이터를 한 번만 보내고 이후 서버로부터 오는 데이터 출력
    sio.connect('http://192.168.9.115:3000')  # MagicMirror 서버의 IP 주소로 변경
    sio.emit('car2', "id값")  # 문자열 데이터를 서버로 전송
    print('id값 전송')
    sio.wait()
except KeyboardInterrupt:
    print("프로그램이 종료되었습니다.")
    set_motor_speed(0, 0, 0, 0)  # 모터 정지
    sio.disconnect()
    unexport_gpio(GPIO_PIN1)
    unexport_gpio(GPIO_PIN2)
    unexport_gpio(GPIO_PIN3)
    unexport_gpio(GPIO_PIN4)
    sys.exit(0)