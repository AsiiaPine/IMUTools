import json
# import pandas as pd
from time import sleep
import time
from Motor.libs import Gyems, CanBus

bus = CanBus()
motor = Gyems(bus)

def load_data_from_json(key_str: int|str):
    try:
        with open('motor_speeds.json') as f:
            motor_tests = json.loads(json.load(f))
        for key, val in motor_tests.items():
            if str(key_str) in key:
                motor_tests = val
                return motor_tests
            raise ValueError(f'tests_data do not have such word in keys {key_str}')
        return {}
    except ValueError:
        print(f'tests_data do not have such word in keys {key_str}')
        return {}


tests_data = load_data_from_json(1)
start_time = time.time()
try:
    for params in tests_data:
        motor.enable()
        motor.set_zero()
        angle = params["angle"]

        # Iterate through each row and retrieve values
        speed = params['speed']
        forward = params['forward']
        
        print("angle/speed", angle/speed)
        input()
        start_time = time.time()
        motor.set_angle(forward*angle, int(speed))
        while motor.read_angle() < angle-10:
            print(motor.read_angle())
        print("time", time.time()- start_time)

        if forward == 0:
            print(f"Speed: {-speed}, Forward or not: {forward}")
        else:
            print(f"Speed: {speed}, Forward or not: {forward}")
        sleep(1)



# Close the CAN bus connection
finally:
    motor.disable(True)
    bus.close()