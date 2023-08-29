import cv2
import numpy as np
import os
import socketio
import time
import threading

sio = socketio.Client()

@sio.event
def connect():
    print('서버에 연결되었습니다.')

@sio.event
def disconnect():
    print('서버와 연결이 끊어졌습니다.')

sio.connect('http://192.168.9.115:3000')  # MagicMirror 서버의 IP 주소로 변경

distance_value = 0
distance_lock = threading.Lock()

# motor gpio pin 
gpio_pin1 = 89  # Ringt side motor pin cw
gpio_pin2 = 90  # Right side motor pin ccw
gpio_pin3 = 65  # Left side motor pin cw
gpio_pin4 = 66  # Left side motor pin ccw
TRIG_PIN = 118  # GPIO pin number for trigger output
ECHO_PIN = 120  # GPIO pin number for echo input
data = ""
car_state = ""
cap = cv2.VideoCapture(1)

# set TOPST GPIO directory
gpio_path1 = f"/sys/class/gpio/gpio{gpio_pin1}"
gpio_path2 = f"/sys/class/gpio/gpio{gpio_pin2}"
gpio_path3 = f"/sys/class/gpio/gpio{gpio_pin3}"  
gpio_path4 = f"/sys/class/gpio/gpio{gpio_pin4}" 

# GPIO initialization and release functions
def gpio_setup(pin, direction):
    # Export GPIO
    with open('/sys/class/gpio/export', 'w') as export_file:
        export_file.write(str(pin))

    # Configure direction
    with open(f"/sys/class/gpio/gpio{pin}/direction", 'w') as f:
        f.write(direction)

def gpio_unexport(pin):
    # Unexport GPIO
    with open('/sys/class/gpio/unexport', 'w') as unexport_file:
        unexport_file.write(str(pin))

def gpio_write(pin, value):
    with open(f"/sys/class/gpio/gpio{pin}/value", 'w') as f:
        f.write(str(value))

def gpio_read(pin):
    with open(f"/sys/class/gpio/gpio{pin}/value", 'r') as f:
        return int(f.read())
def measure_distance():
    pulse_start = 0
    pulse_end = 0
    # Initialize ultrasound transmission time
    gpio_write(TRIG_PIN, 0)
    time.sleep(0.2)  # Wait to reset

    gpio_write(TRIG_PIN, 1)
    time.sleep(0.00001)  # Emit ultrasound for 10 microseconds
    gpio_write(TRIG_PIN, 0)

    # Timing the echo pulse
    while gpio_read(ECHO_PIN) == 0:
        pulse_start = time.time()

    while gpio_read(ECHO_PIN) == 1:
        pulse_end = time.time()
        
    pulse_duration = pulse_end - pulse_start

    # Calculate distance (speed of sound is 343m/s)
    distance = pulse_duration * 17150

    return distance

def ultrasonic_thread():
    global distance_value
    while True:
        distance = measure_distance()
        with distance_lock:
            distance_value = distance
        time.sleep(0.5)  # 적절한 간격으로 거리 측정

def set_motor_speed(gpio_num1, gpio_num2, gpio_num3, gpio_num4, speed1, speed2, speed3, speed4):
    with open(f"/sys/class/gpio/gpio{gpio_num1}/value", "w") as file1:
        file1.write(str(speed1))

    with open(f"/sys/class/gpio/gpio{gpio_num2}/value", "w") as file2:
        file2.write(str(speed2))

    with open(f"/sys/class/gpio/gpio{gpio_num3}/value", "w") as file3:
        file3.write(str(speed3))

    with open(f"/sys/class/gpio/gpio{gpio_num4}/value", "w") as file4:
        file4.write(str(speed4))

def DetectLineSlope(src):
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    can = cv2.Canny(gray, 50, 200, None, 3)
    height = can.shape[0]
    rectangle = np.array([[(0, height), (120, 300), (520, 300), (640, height)]])
    mask = np.zeros_like(can)
    cv2.fillPoly(mask, rectangle, 255)
    masked_image = cv2.bitwise_and(can, mask)
    ccan = cv2.cvtColor(masked_image, cv2.COLOR_GRAY2BGR)
    mimg = src.copy()

    line_arr = cv2.HoughLinesP(masked_image, 1, np.pi / 180, 20, minLineLength=10, maxLineGap=10)

    if line_arr is None:
        print('stop')
        set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
        data = "S"
        sio.emit('car', data)  # 문자열 데이터를 서버로 전송
        degree_L = 0
        degree_R = 0
    else:
        line_arr2 = np.empty((len(line_arr), 5), int)
        for i in range(len(line_arr)):
            l = line_arr[i][0]
            line_arr2[i] = np.append(line_arr[i], np.array((np.arctan2(l[1] - l[3], l[0] - l[2]) * 180) / np.pi))

        line_L = line_arr2[line_arr2[:, 0] < 320]
        line_R = line_arr2[line_arr2[:, 0] > 320]

        if len(line_L) > 0:
            line_L = line_L[np.argmax(line_L[:, 0])]
            degree_L = line_L[4]
            cv2.line(ccan, (line_L[0], line_L[1]), (line_L[2], line_L[3]), (0, 0, 255), 10, cv2.LINE_AA)
        else:
            degree_L = 0

        if len(line_R) > 0:
            line_R = line_R[np.argmin(line_R[:, 0])]
            degree_R = line_R[4]
            cv2.line(ccan, (line_R[0], line_R[1]), (line_R[2], line_R[3]), (255, 0, 0), 10, cv2.LINE_AA)
        else:
            degree_R = 0

    mimg = cv2.addWeighted(src, 1, ccan, 1, 0)
    return mimg, degree_L, degree_R, rectangle

@sio.on('Car_State')  # 'Car_State' 이벤트 수신
def receive_car_state(data):
    global car_state  # Declare car_state as a global variable
    car_state = data  # Update car_state based on the received data
    print("Received car state:", car_state)

def car():
        # video capture reset
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.resize(frame, (640, 360))
            mimg, l, r, rectangle = DetectLineSlope(frame)
            cv2.polylines(mimg, [np.int32(rectangle)], True, (0, 255, 0), thickness=2)
            cv2.imshow('car', mimg)
            receive_car_state(car_state)
            with distance_lock:
                current_distance = distance_value
            print(f"Distance: {current_distance:.2f} cm")
            if car_state == 'start':
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                elif current_distance < 50:
                    print('stop')
                    set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
                    data = "S"
                    sio.emit('beep', data)

                else:
                    if abs(l) <= 155 or abs(r) <= 155:
                        if l == 0 or r == 0:
                            if l < 0 or r < 0:
                                print('left')
                                set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 1, 0, 0, 1)
                                data = "L"
                                sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                            elif l > 0 or r > 0:
                                print('right')
                                set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 1, 1, 0)
                                data = "R"
                                sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                        elif abs(l - 15) > abs(r):
                            print('right')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 1, 1, 0)
                            data = "R"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                        elif abs(r + 15) > abs(l):
                            print('left')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 1, 0, 0, 1)
                            data = "L"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                        else:
                            print('go')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 1, 0, 1, 0)
                            data = "F"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                    else:
                        if l > 155 or r > 155:
                            print('hard left')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 1, 0, 0, 1)
                            data = "L"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                        elif l < -155 or r < -155:
                            print('hard right')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 1, 1, 0)
                            data = "R"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                        else:
                            print('stop')
                            set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
                            data = "S"
                            sio.emit('car', data)  # 문자열 데이터를 서버로 전송
            else:
                print('stop')
                set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
                data = "S"
                sio.emit('car', data)  # 문자열 데이터를 서버로 전송
                
        
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping motors.")
        set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
        cap.release()
        cv2.destroyAllWindows()
        gpio_unexport(gpio_pin1)
        gpio_unexport(gpio_pin2)
        gpio_unexport(gpio_pin3)
        gpio_unexport(gpio_pin4)
        gpio_unexport(TRIG_PIN)
        gpio_unexport(ECHO_PIN)
        set_motor_speed(gpio_pin1, gpio_pin2, gpio_pin3, gpio_pin4, 0, 0, 0, 0)
        cap.release()
        cv2.destroyAllWindows()



if __name__ == '__main__':
    # GPIO reset
    sio.emit('car1', "id값")  # 문자열 데이터를 서버로 전송
    print('car1id값 전송')
    gpio_setup(gpio_pin1, 'out')
    gpio_setup(gpio_pin2, 'out')
    gpio_setup(gpio_pin3, 'out')
    gpio_setup(gpio_pin4, 'out')
    gpio_setup(TRIG_PIN, 'out')
    gpio_setup(ECHO_PIN, 'in')
    ultrasonic_thread = threading.Thread(target=ultrasonic_thread, daemon=True)
    ultrasonic_thread.start()
    car()