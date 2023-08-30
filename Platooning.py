import socketio
import sys
import os

# GPIO pin 상수 정의
GPIO_PIN1 = 89  # Right side motor pin cw
GPIO_PIN2 = 90  # Right side motor pin ccw
GPIO_PIN3 = 65  # Left side motor pin cw
GPIO_PIN4 = 66  # Left side motor pin ccw
pwm_pin = 2
pwm_path = "/sys/class/pwm/pwmchip0/"

sio = socketio.Client()

# PWM control functions
def enable_pwm(pwm_pin):
    with open(pwm_path + 'export', 'w') as export_file:
        export_file.write(str(pwm_pin))

def disable_pwm(pwm_pin):
    with open(pwm_path + 'unexport', 'w') as unexport_file:
        unexport_file.write(str(pwm_pin))

def set_pwm(pwm_pin, duty_cycle):
    with open(os.path.join(pwm_path, f"pwm{pwm_pin}/period"), "w") as period_file:
        period_file.write("2000000")  # 1MHz period

    with open(os.path.join(pwm_path, f"pwm{pwm_pin}/duty_cycle"), "w") as duty_cycle_file:
        duty_cycle_value = int(duty_cycle * 10000)  # Scale 0-100 to duty cycle
        duty_cycle_file.write(str(duty_cycle_value))

    with open(os.path.join(pwm_path, f"pwm{pwm_pin}/enable"), "w") as enable_file:
        enable_file.write("1")

# PWM 정지
def stop_pwm(pwm_pin):
    with open(os.path.join(pwm_path, f"pwm{pwm_pin}/enable"), "w") as enable_file:
        enable_file.write("0")

# GPIO 출력을 조절하여 모터를 제어하는 함수
def set_motor_speed(gpio_num1, gpio_num2, gpio_num3, gpio_num4, speed1, speed2, speed3, speed4):
    with open(f"/sys/class/gpio/gpio{gpio_num1}/value", "w") as file1:
        file1.write(str(speed1))

    with open(f"/sys/class/gpio/gpio{gpio_num2}/value", "w") as file2:
        file2.write(str(speed2))

    with open(f"/sys/class/gpio/gpio{gpio_num3}/value", "w") as file3:
        file3.write(str(speed3))

    with open(f"/sys/class/gpio/gpio{gpio_num4}/value", "w") as file4:
        file4.write(str(speed4))

@sio.event
def connect():
    print('서버에 연결되었습니다.')

@sio.event
def disconnect():
    print('서버와 연결이 끊어졌습니다.')

@sio.on('Car_State')  # 'start' 이벤트 수신
def receive_start_data(data):
    print("Received start data:", data)
    process_received_data(data)

def process_received_data(data):
    try:
        if data == 'L':
            set_motor_speed(1, 0, 0, 1)
        elif data == 'R':
            set_motor_speed(0, 1, 1, 0)
        elif data == 'HL':
            set_motor_speed(1, 0, 0, 1)
            set_pwm(pwm_pin,60)
        elif data == 'HR':
            set_motor_speed(0, 1, 1, 0)
            set_pwm(pwm_pin,60)
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

try:
    # GPIO 초기화 및 설정
    export_gpio(GPIO_PIN1)
    export_gpio(GPIO_PIN2)
    export_gpio(GPIO_PIN3)
    export_gpio(GPIO_PIN4)
    enable_pwm(pwm_pin)

    set_gpio_direction(GPIO_PIN1, "out")
    set_gpio_direction(GPIO_PIN2, "out")
    set_gpio_direction(GPIO_PIN3, "out")
    set_gpio_direction(GPIO_PIN4, "out")
    # 데이터를 한 번만 보내고 이후 서버로부터 오는 데이터 출력
    sio.connect('http://192.168.9.115:3000')  # MagicMirror 서버의 IP 주소로 변경
    # PWM 설정
    set_pwm(pwm_pin,40)  # 50% duty cycle
    sio.emit('car2', "id값")  # 문자열 데이터를 서버로 전송
    print('id값 전송')
    sio.wait()
except KeyboardInterrupt:
    print("프로그램이 종료되었습니다.")
    set_motor_speed(0, 0, 0, 0)  # 모터 정지
    stop_pwm(pwm_pin)
    disable_pwm(pwm_pin)
    sio.disconnect()
    unexport_gpio(GPIO_PIN1)
    unexport_gpio(GPIO_PIN2)
    unexport_gpio(GPIO_PIN3)
    unexport_gpio(GPIO_PIN4)
    sys.exit(0)