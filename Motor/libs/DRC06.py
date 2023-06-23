from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List

from can import Message

from .interface import CanBus

# MOTOR ID 0x140 + (1~32)

MOTOR_ID = 0x141

# COMMAND BYTES

READ_PID = 0x30
WRITE_PID_TO_RAM = 0x31
WRITE_PID_TO_ROM = 0x32
READ_ACCELERATION = 0x33
WRITE_ACCELERATION = 0x34

READ_ENCODER = 0x90
WRITE_ENCODER_OFFSET = 0x91
READ_MULTI_TURN_ANGLE = 0x92
READ_SINGLE_CIRCLE_ANGLE = 0x94

WRITE_CURRENT_POSITION = 0x19

READ_MOTOR_STATUS_1 = 0x9A
CLEAR_MOTOR_ERROR = 0x9B
READ_MOTOR_STATUS_2 = 0x9C
READ_MOTOR_STATUS_3 = 0x9D

MOTOR_OFF = 0x80
MOTOR_STOP = 0x81
MOTOR_RUN = 0x88

TORQUE_CLOSED_LOOP = 0xA1
SPEED_CLOSED_LOOP = 0xA2
POSITION_CLOSED_LOOP_1 = 0xA3
POSITION_CLOSED_LOOP_2 = 0xA4
POSITION_CLOSED_LOOP_3 = 0xA5
POSITION_CLOSED_LOOP_4 = 0xA6


class Storage(Enum):
    ROM = 0
    RAM = 1


@dataclass
class PID:
    name: str
    kp: float
    ki: float


class DRC06:

    def __init__(self, bus: CanBus, motor_id: int | None = None, max_torque: float = 6) -> None:
        self.bus = bus.bus
        self.motor_id = motor_id if motor_id is not None else MOTOR_ID
        self.max_torque = max_torque

    @staticmethod
    def mapper(value: float, i_low: float, i_high: float, o_low: float, o_high) -> float:
        return value / (i_high - i_low) * (o_high - o_low)

    def request(self, data: List[int]) -> Message:
        """
        The request function sends a message to the motor and waits for a response.
        The function takes in an array of 8 integers, which are sent as the data payload of the CAN message.
        It returns another Message object containing the response from the motor.

        :param data: List[int]: Pass the data to be sent to the motor
        :return: A message
        :doc-author: Trelent
        """
        msg = Message(arbitration_id=self.motor_id, data=data, dlc=8, is_extended_id=False)
        self.bus.send(msg)
        while True:
            response = self.bus.recv(0.1)
            if response:
                if response.arbitration_id == self.motor_id:
                    return response

    def read_pid(self) -> Tuple[PID, PID, PID]:
        """
            The read_pid function reads the current PID values from the motor controller.
            The function returns a list of integers, where each integer is one byte of data.

        :return: Tuple[PID, PID, PID]: PID("angle_pid"), PID("speed_pid"), PID("torque_pid")
        :doc-author: Trelent
        """
        data = [READ_PID, *([0] * 7)]
        response = list(self.request(data).data[2:])
        return (
            PID("angle_pid", response[0] * 3 / 256, response[1] * 0.1 / 256),
            PID("speed_pid", response[2] * 0.1 / 256, response[3] * 0.01 / 256),
            PID("torque_pid", response[4] * 0.1 / 256, response[5] * 0.01 / 256)
        )

    def write_pid(
        self,
        angle_pid: PID,
        speed_pid: PID,
        torque_pid: PID,
        storage: Storage = Storage.RAM
    ) -> Tuple[PID, PID, PID]:
        """
        The write_pid function writes the PID values to either RAM or ROM.
        Args:
            angle_pid (PID): The PID object for the angle control loop.
            speed_pid (PID): The PID object for the speed control loop.
            torque_pid (PID): The PID object for the torque control loop.

        :param angle_pid: PID: Set the angle pid values
        :param speed_pid: PID: Set the speed pid values
        :param torque_pid: PID: Set the torque pid values
        :param storage: Storage: Determine whether the pid values are written to ram or rom
        :return: The same pid values that were sent
        :doc-author: Trelent
        """
        if angle_pid.kp > 3 or angle_pid.ki > 0.1 or speed_pid.kp > 0.1 or speed_pid.ki > 0.01 or torque_pid.kp > 0.1 or torque_pid.ki > 0.01:
            raise ValueError("Some of PID vars are invalid")

        akp, aki = int(angle_pid.kp * 256 / 3), int(angle_pid.ki * 256 / 0.1)
        skp, ski = int(speed_pid.kp * 256 / 0.1), int(speed_pid.ki * 256 / 0.01)
        tkp, tki = int(torque_pid.kp * 256 / 0.1), int(torque_pid.ki * 256 / 0.01)
        if storage == Storage.RAM:
            data = [WRITE_PID_TO_RAM, 0, akp, aki, skp, ski, tkp, tki]
        elif storage == Storage.ROM:
            data = [WRITE_PID_TO_ROM, 0, akp, aki, skp, ski, tkp, tki]
        else:
            raise ValueError("You set invalid storage type")

        response = list(self.request(data).data[2:])
        return (
            PID("angle_pid", response[0] * 3 / 256, response[1] * 0.1 / 256),
            PID("speed_pid", response[2] * 0.1 / 256, response[3] * 0.01 / 256),
            PID("torque_pid", response[4] * 0.1 / 256, response[5] * 0.01 / 256)
        )

    def read_acceleration(self) -> int:
        """
        The read_acceleration function reads the acceleration of the robot.

        :return: An integer Acceleration
        :doc-author: Trelent
        """
        data = [READ_ACCELERATION, *([0] * 7)]
        response = list(self.request(data).data[4:])
        return int.from_bytes(response, byteorder="little", signed=False)

    def write_acceleration(self, accel: int) -> int:
        """
        The write_acceleration function writes the acceleration value to the motor.

        :param accel: int: Set the acceleration of the motor
        :return: The acceleration value that was written to the device
        :doc-author: Trelent
        """
        buffer = list(int.to_bytes(accel, 4, "little", signed=False))
        data = [WRITE_ACCELERATION, 0, 0, 0, *buffer]
        response = list(self.request(data).data[4:])
        return int.from_bytes(response, byteorder="little", signed=False)

    def read_encoder(self) -> Tuple[int, int, int]:
        """
        The read_encoder function reads the encoder values from the motor controller.
        The function returns a tuple of three integers, each representing one of the motors' encoder values.

        :return: (Encoder Position, Encoder Original Position, Encoder Offset)
        :doc-author: Trelent
        """
        data = [READ_ENCODER, *([0] * 7)]
        response = list(self.request(data).data[2:])
        return (
            int.from_bytes(response[:2], "little", signed=False),
            int.from_bytes(response[2:4], "little", signed=False),
            int.from_bytes(response[4:], "little", signed=False)
        )

    def write_encoder_offset(self, offset: int) -> int:
        """
        The write_encoder_offset function writes the encoder offset to the motor controller.
        The encoder offset is used to set a new zero position for the encoder. The value written
        to this register will be added to all future position measurements, and subtracted from all
        future velocity measurements.

        :param offset: int: Set the encoder offset
        :return: The offset that was written to the encoder
        :doc-author: Trelent
        """
        buffer = list(int.to_bytes(offset, 2, "little", signed=False))
        data = [WRITE_ENCODER_OFFSET, 0, 0, 0, 0, 0, *buffer]
        response = list(self.request(data).data[6:])
        return int.from_bytes(response, "little", signed=False)

    def set_motor_position_zero(self) -> int:
        """
        The set_motor_position_zero function sets the current position of the motor to zero.

        :return: Encoder offset
        :doc-author: Trelent
        """
        data = [WRITE_CURRENT_POSITION, *([0] * 7)]
        response = list(self.request(data).data[6:])
        return int.from_bytes(response, "little", signed=False)

    def read_multi_turns_angle(self) -> float:
        """
        The read_multi_turns_angle function reads the current angle of the motor in degrees.

        :return: An integer value of the current angle
        :doc-author: Trelent
        """
        data = [READ_MULTI_TURN_ANGLE, *([0] * 7)]
        response = list(self.request(data).data[1:])
        return int.from_bytes(response, "little", signed=True) * 0.01

    def read_single_circle_angle(self) -> float:
        """
        The read_single_circle_angle function reads the angle of a single circle.

        :return: The angle of the current position
        :doc-author: Trelent
        """
        data = [READ_SINGLE_CIRCLE_ANGLE, *([0] * 7)]
        response = list(self.request(data).data[6:])
        return int.from_bytes(response, "little", signed=True) * 0.01

    def motor_off(self) -> None:
        """
        The motor_off function turns off the motor.

        :return: None
        :doc-author: Trelent
        """
        data = [MOTOR_OFF, *([0] * 7)]
        self.request(data)

    def motor_stop(self) -> None:
        """
        The motor_stop function stops the motor.

        :return: None
        :doc-author: Trelent
        """
        data = [MOTOR_STOP, *([0] * 7)]
        self.request(data)

    def motor_running(self) -> None:
        """
        The motor_running function is used to check if the motor is running.

        :return: None
        :doc-author: Trelent
        """
        data = [MOTOR_RUN, *([0] * 7)]
        self.request(data)

    def read_motor_status_1(self) -> Tuple[int, float, int]:
        """
        The read_motor_status_1 function reads the motor status 1.

        :return: A tuple with the temperature, voltage and error state
        :doc-author: Trelent
        """
        data = [READ_MOTOR_STATUS_1, *([0] * 7)]
        response = list(self.request(data).data)
        temp = response[1]
        voltage = int.from_bytes(response[3:5], "little", signed=False) * 0.1
        error_state = response[-1]
        return temp, voltage, error_state

    def clear_motor_error(self) -> Tuple[int, float, int]:
        """
        The clear_motor_error function clears the motor error state.

        :return: A tuple of three values, the first being a temperature value, the second being a voltage value and the third being an error state
        :doc-author: Trelent
        """
        data = [CLEAR_MOTOR_ERROR, *([0] * 7)]
        response = list(self.request(data).data)
        temp = response[1]
        voltage = int.from_bytes(response[3:5], "little", signed=False) * 0.1
        error_state = response[-1]
        return temp, voltage, error_state

    def read_motor_status_2(self) -> Tuple[int, float, int, int]:
        """
        The read_motor_status_2 function reads the motor status 2 register.
                The function returns a tuple of 4 values:
                    - Temperature (Celsius)
                    - Torque (A)
                    - Speed (RPM)
                    - Encoder position

        :return: A tuple of 4 values:
        :doc-author: Trelent
        """
        data = [READ_MOTOR_STATUS_2, *([0] * 7)]
        response = list(self.request(data).data)

        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        speed = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, speed, encoder

    def read_motor_status_3(self) -> Tuple[float, float, float]:
        """
        The read_motor_status_3 function returns the current motor status.

        :return: The current of each phase
        :doc-author: Trelent
        """
        data = [READ_MOTOR_STATUS_3, *([0] * 7)]
        response = list(self.request(data).data)
        phase_a = int.from_bytes(response[2:4], "little", signed=True) / 64
        phase_b = int.from_bytes(response[4:6], "little", signed=True) / 64
        phase_c = int.from_bytes(response[6:], "little", signed=True) / 64

        return phase_a, phase_b, phase_c

    def set_torque(self, torque: float) -> Tuple[int, float, int, int]:
        """
        The set_torque function takes in a torque value and sets the motor to that torque.
        The function returns a tuple of (temperature, current_torque, speed, encoder).

        :param torque: float: Set the torque of the motor
        :return: A tuple of 4 values
        :doc-author: Trelent
        """
        torque = self.mapper(torque, -self.max_torque, self.max_torque, -2000, 2000)
        buffer = list(int.to_bytes(int(torque), 2, "little", signed=True))
        data = [TORQUE_CLOSED_LOOP, 0, 0, 0, *buffer, 0, 0]
        response = list(self.request(data).data)

        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        speed = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, speed, encoder

    def set_speed(self, velocity: float) -> Tuple[int, float, int, int]:
        """
        The set_speed function takes in a velocity value and returns the temperature, torque, speed, and encoder values.

        :param velocity: float: Set the speed of the motor
        :return: A tuple of 4 values
        :doc-author: Trelent
        """
        buffer = list(int.to_bytes(int(velocity / 0.01), 4, "little", signed=True))
        data = [SPEED_CLOSED_LOOP, 0, 0, 0, *buffer]
        response = list(self.request(data).data)
        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        speed = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, speed, encoder

    def set_angle(self, angle: float) -> Tuple[int, float, int, int]:
        """
        The set_angle function takes in an angle and returns a tuple of the temperature, torque, speed, and encoder values.

        :param angle: float: Set the angle of the servo
        :return: A tuple of 4 values
        :doc-author: Trelent
        """
        buffer = list(int.to_bytes(int(angle / 0.01), 4, "little", signed=True))
        data = [POSITION_CLOSED_LOOP_1, 0, 0, 0, *buffer]
        response = list(self.request(data).data)
        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        speed = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, speed, encoder

    def set_angle_with_max_speed(self, angle: float, max_speed: int) -> Tuple[int, float, int, int]:
        """
        The set_angle_with_max_speed function takes in an angle and a max speed, then returns the temperature of the motor,
        the torque of the motor, the speed of rotation (in RPM), and encoder value.

        :param angle: float: Set the angle of the servo
        :param max_speed: int: Set the maximum speed of the motor
        :return: The temperature, torque, speed and encoder
        :doc-author: Trelent
        """
        speed = list(int.to_bytes(max_speed, 2, "little", signed=False))
        buffer = list(int.to_bytes(int(angle / 0.01), 4, "little", signed=True))
        data = [POSITION_CLOSED_LOOP_2, 0, *speed, *buffer]
        response = list(self.request(data).data)
        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        velocity = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, velocity, encoder

    def set_angle_with_direction(self, angle: float, direction: int = 0x00) -> Tuple[int, float, int, int]:
        """
        The set_angle_with_direction function is used to set the angle of the servo motor.
            The function takes in an angle and a direction as parameters, and returns a tuple containing:
                - temperature (int)
                - torque (float)
                - speed (int)
                - encoder value (int).

        :param angle: float: Set the angle of the servo
        :param direction: int: Set the direction of rotation
        :return: The temperature, torque, speed and encoder
        :doc-author: Trelent
        """
        if 0 > angle or angle > 359.99:
            raise ValueError("Angle is out of the range (0~359.99)")

        buffer = list(int.to_bytes(int(angle / 0.01), 2, "little", signed=False))
        data = [POSITION_CLOSED_LOOP_3, direction, 0, 0, *buffer, 0, 0]
        response = list(self.request(data).data)
        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        speed = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, speed, encoder

    def set_angle_with_direction_with_max_speed(self, angle: float, max_speed: int, direction: int = 0x00) -> Tuple[
        int, float, int, int]:
        """
        The set_angle_with_direction_with_max_speed function is used to set the angle of the servo motor.

        :param angle: float: Set the angle of the servo
        :param max_speed: int: Set the maximum speed of the motor
        :param direction: int: Set the direction of rotation
        :return: A tuple of 4 values
        :doc-author: Trelent
        """
        if 0 > angle or angle > 359.99:
            raise ValueError("Angle is out of the range (0~359.99)")

        speed = list(int.to_bytes(int(max_speed / 0.01), 2, "little", signed=False))
        buffer = list(int.to_bytes(int(angle / 0.01), 2, "little", signed=False))
        data = [POSITION_CLOSED_LOOP_4, direction, *speed, *buffer, 0, 0]
        response = list(self.request(data).data)
        temp = response[1]
        torque = self.mapper(int.from_bytes(response[2:4], "little", signed=True), -2048, 2048, -self.max_torque,
                             self.max_torque)
        velocity = int.from_bytes(response[4:6], "little", signed=True)
        encoder = int.from_bytes(response[6:], "little", signed=False)
        return temp, torque, velocity, encoder
