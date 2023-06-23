from dataclasses import dataclass
from typing import Callable, Optional, Any, TypeVar

from .DRC06 import DRC06, PID, Storage
from .interface import CanBus
from .utils import *
from copy import deepcopy



@dataclass
class MotorStatus:
    nominal_voltage: float
    nominal_temperature: int

    is_normal_voltage: bool = True
    is_normal_temperature: bool = True
    is_active: bool = False

    def __str__(self):
        return (
            f"""
            {"=" * 50}
            Motor status:

                Current Voltage (V): {self.nominal_voltage:.2f}
                Current Temperature (C°): {self.nominal_temperature}
                Active: {"True" if self.is_active else "False"}

            Error status:

                Voltage: {"Normal" if self.is_normal_voltage else "Low voltage protection"}
                Temperature: {"Normal" if self.is_normal_temperature else "Over temperature protection"}
            {"=" * 50}
            """
        )


# def protection(func: Callable[..., Any]) -> Callable[..., Optional[Callable[..., Any]]]:
def protection(func: Callable[..., Any])->Callable[..., Any|None]:
    def wrap(self, *args, **kwargs)-> Any | None:
        if self.check_status():
            return func(self, *args, **kwargs)
        if not self.status.is_active:
            print(f"INFO: Motor is not active")
        if not self.status.is_normal_voltage or self.status.nominal_temperature:
            print(f"ERROR: Motor has error with voltage or with temperature")
            if self.status.is_active:
                self.disable(True)
        return None

    return wrap


class Gyems:

    def __init__(self, bus: CanBus, motor_id: int |None = None, max_torque: float = 6) -> None:
        self.status = MotorStatus(0, 0)
        self.state = {
            "torque": 0.0,
            "speed": 0.0,
            "phase_a": 0.0,
            "phase_b": 0.0,
            "phase_c": 0.0,
            "angle": 0.0,
            "encoder": 0.0,
            "rotations": 0,
            "voltage": 0.0,
            "temperature": 0,
        }
        self.max_torque = max_torque
        self.driver = DRC06(bus, motor_id, max_torque)
        self.encoder_ratio = 16383
        self.encoder_steps = 0
        self.encoder = 0

    def check_status(self) -> bool:
        """
        The check_status function checks the status of the device.

        :return: A boolean value
        :doc-author: Trelent
        """
        return self.status.is_active and self.status.is_normal_temperature and self.status.is_normal_voltage

    def enable(self) -> None:
        """
        The enable function enables the motor.

        :return: Nothing
        :doc-author: Trelent
        """
        self.driver.motor_running()

        temp, voltage, error_code = self.driver.clear_motor_error()
        is_vol, is_temp = decode_error(error_code)
        self.status = MotorStatus(voltage, temp, is_vol, is_temp, is_vol and is_temp)

    def disable(self, is_off: bool = False) -> None:
        """
        The disable function stops the motor and turns it off.

        :param is_off: bool: Determine whether the motor should be turned off or not
        :return: None
        :doc-author: Trelent
        """
        self.driver.motor_stop()
        print("INFO: Motor stop")
        if is_off:
            self.driver.motor_off()
            print("INFO: Motor off")
        self.status.is_active = False

    @protection
    def set_zero(self) -> bool:
        """
        The set_zero function sets the motor position to zero.
                It returns True if the offset was successfully written to the encoder, and False otherwise.

        :return: A boolean value, either true or false
        :doc-author: Trelent
        """
        offset = self.driver.set_motor_position_zero()
        offset_motor = self.driver.write_encoder_offset(offset)
        return offset == offset_motor

    @protection
    def set_current(self, current: float) -> dict | None:
        """
        The set_current function sets the current of the motor.

        :param current: float: Set the current of the motor
        :return: returns a dictionary of the current state
        :doc-author: Trelent
        """
        current = limiter(current, self.max_torque)
        self.driver.set_torque(current)
        return self.info()

    @protection
    def set_speed(self, velocity: float) -> dict | None:
        """
        The set_speed function sets the speed of the car.

        :param velocity: float: Set the speed of the vehicle
        :return: returns a dictionary of the current state
        :doc-author: Trelent
        """
        self.driver.set_speed(velocity)
        return self.info()

    @protection
    def set_angle(self, angle: float, max_speed: int| None = None, direction: bool | None = None) -> dict | None:
        """
        The set_angle function sets the angle of the servo motor.

        :param angle: float: Set the angle of the servo
        :param max_speed: int: Set the maximum speed of the servo
        :param direction: bool: Set the direction of rotation
        :return: returns a dictionary of the current state
        :doc-author: Trelent
        """
        if max_speed is None and direction is None:
            self.driver.set_angle(angle)
        elif max_speed is not None and direction is None:
            self.driver.set_angle_with_max_speed(angle, max_speed)
        elif max_speed is None and direction in [0, 1]:
            self.driver.set_angle_with_direction(angle, direction)
        elif max_speed is not None and direction in [0, 1]:
            self.driver.set_angle_with_direction_with_max_speed(angle, max_speed, direction)
        else:
            self.driver.set_angle(angle)
        return self.info()

    @protection
    def read_angle(self, single_circle: bool = False) -> float:
        """
        The read_angle function reads the angle of the encoder.

        :param single_circle: bool: Determine whether the encoder is single-turn or multi-turn
        :return: The angle of the motor
        :doc-author: Trelent
        """
        if single_circle:
            return self.driver.read_single_circle_angle()
        return self.driver.read_multi_turns_angle()

    @protection
    def read_encoder(self) -> int:
        """
        The read_encoder function reads the encoder value from the driver and returns it.
        The function also updates self.encoder_steps if necessary, which is used to keep track of how many times
        the encoder has wrapped around.

        :return: The value of the encoder
        :doc-author: Trelent
        """
        encoder, *_ = self.driver.read_encoder()
        if encoder < self.encoder:
            self.encoder_steps += 1
        self.encoder = encoder
        return self.encoder_ratio * self.encoder_steps + self.encoder

    @protection
    def read_pid(self) -> Tuple[PID, PID, PID]:
        """
        The read_pid function reads the current PID values from the driver.

        :return: A tuple of the pid values for the current
        :doc-author: Trelent
        """
        return self.driver.read_pid()

    @protection
    def write_pid(self, angle: PID, speed: PID, torque: PID, storage: Storage = Storage.RAM) -> Tuple[PID, PID, PID]:
        """
        The write_pid function writes the PID values to the motor.

        :param angle: PID: Set the angle pid values
        :param speed: PID: Set the pid values for the speed of the motor
        :param torque: PID: Set the torque pid values
        :param storage: Storage: Specify whether the pid values are stored in ram or rom
        :return: The values that were written to the controller
        :doc-author: Trelent
        """
        return self.driver.write_pid(angle, speed, torque, storage)

    @protection
    def read_acceleration(self) -> int:
        """
        The read_acceleration function reads the acceleration of the motor.

        :return: The current acceleration of the motor
        :doc-author: Trelent
        """
        return self.driver.read_acceleration()

    @protection
    def write_acceleration(self, accel: int) -> int:
        """
        The write_acceleration function sets the acceleration of the motor.

        :param accel: int: Set the acceleration of the stepper motor
        :return: The value of the acceleration
        :doc-author: Trelent
        """
        return self.driver.write_acceleration(accel)

    @protection
    def info(self) -> dict:
        """
        The info function returns a dictionary of the current state of the motor.

        :return: A dictionary with the following keys:
        :doc-author: Trelent
        """
        angle = self.driver.read_multi_turns_angle()
        encoder = self.read_encoder()

        temp, voltage, error_code = self.driver.read_motor_status_1()
        _, torque, speed, _ = self.driver.read_motor_status_2()
        phase_a, phase_b, phase_c = self.driver.read_motor_status_3()
        is_vol, is_temp = decode_error(error_code)

        self.status = MotorStatus(voltage, temp, is_vol, is_temp, is_vol and is_temp)
        self.state["torque"] = torque
        self.state["phase_a"] = phase_a
        self.state["phase_b"] = phase_b
        self.state["phase_c"] = phase_c
        self.state["speed"] = speed / 10
        self.state["angle"] = angle
        self.state["encoder"] = encoder if encoder is not None else self.encoder
        self.state["rotations"] = self.encoder_steps
        self.state["voltage"] = voltage
        self.state["temperature"] = temp

        return deepcopy(self.state)
