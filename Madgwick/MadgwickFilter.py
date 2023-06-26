from typing import Any
import numpy as np

from Madgwick.quaternion_calculation import *
import time


class MadgwickAHRS:
    """ MadgwickAHRS class for orientation estimation using the Madgwick algorithm.

    Args: 
    omega_e (float): gyroscope noise in rad/s. 
    sample_period (float, optional): sampling period in seconds. Defaults to 1/256. 
    quaternion (np.ndarray, optional): initial quaternion. Defaults to np.array([1.0, 0.0, 0.0, 0.0], dtype=float). 
    beta (np.ndarray, optional): gyroscope measurement error. Defaults to np.ones(4). 
    hpf (float, optional): high-pass filter cutoff frequency. Defaults to 0.

    Attributes: 
    prev_time (float): previous time stamp. 
    quaternion (np.ndarray): current quaternion. 
    prev_quaternion (np.ndarray): previous quaternion. 
    beta (np.ndarray): algorithm gain. 
    hpf (float): high-pass filter cutoff frequency. 
    acc (np.ndarray): accelerometer data. 
    gyr (np.ndarray): gyroscope data. 
    qDot_omega (np.ndarray): rate of change of quaternion due to gyroscope data. 
    qDot (np.ndarray): rate of change of quaternion.

    Methods: 
    update_IMU(gyros_data: np.ndarray, accel_data: np.ndarray): updates the quaternion using gyroscope and accelerometer data. 
    async_update_IMU(gyros_data: np.ndarray, accel_data: np.ndarray): asynchronous version of update_IMU method. """

    def __init__(self, omega_e, sample_period=1 / 256, quaternion=None, beta: np.ndarray = np.ones(4), hpf=0):
        if quaternion is None:
            quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
        self.prev_time: float = time.time()
        self.quaternion: np.ndarray = quaternion
        self.prev_quaternion: np.ndarray = quaternion

        if beta is np.zeros(4):
            beta = np.sqrt(3)/2 * omega_e
        self.beta: np.ndarray = beta
        self.hpf: float = hpf

        self.acc = np.zeros(3)
        self.gyr = np.zeros(3)

    def update_IMU(self, gyros_data: np.ndarray, accel_data: np.ndarray):
        """ updates the quaternion using gyroscope and accelerometer data. 
        Args:
        gyros_data (np.ndarray): gyroscope data in rad/s.
        accel_data (np.ndarray): accelerometer data in m/s^2"""

        curr_time = time.time()
        self.acc = accel_data
        self.gyr = gyros_data
        q: np.ndarray = self.quaternion
        assert accel_data is not None
        assert gyros_data is not None

        # Gradient decent algorithm corrective step
        F: np.ndarray = np.array([2 * (q[1] * q[3] - q[0] * q[2]) - accel_data[0],
                                  2 * (q[0] * q[1] + q[2] * q[3]) -
                                  accel_data[1],
                                  2 * (0.5 - q[1] ** 2 - q[2] ** 2) - accel_data[2]])

        j1: list[float] = [-2 * q[2], 2 * q[3], -2 * q[0], 2 * q[1]]
        j2: list[float] = [2 * q[1], 2 * q[0], 2 * q[3], 2 * q[2]]
        j3 : list[float] = [0, -4 * q[1], -4 * q[2], 0]
        
        J: np.ndarray = np.array([j1, j2, j3])

        tolerance = 0.01
        step: np.ndarray = (J.T @ F).flatten()
        # normalise step magnitude
        step = - normalize(step, tolerance=tolerance)
        if np.linalg.norm(step) < 0.001:
            return
        # normalise step magnitude
        step = - step/np.linalg.norm(step)

        # Compute rate of change of quaternion
        qDot_omega = get_q_dot(q, gyros_data * 180/np.pi)
        self.qDot_omega = qDot_omega
        qDot: np.ndarray = qDot_omega + self.beta * step * 0.1

        self.qDot = qDot

        dt = curr_time - self.prev_time
        # Integrate to yield quaternion
        q = quaternion_exponential_integration(
            q=q, omega_=qDot, dt=dt)
        norm = np.linalg.norm(q)
        if norm > 0.8 and norm < 1.2:
            self.quaternion = q/norm
        self.prev_time = curr_time

    async def async_update_IMU(self, gyros_data: np.ndarray, accel_data: np.ndarray):
        curr_time = time.time()
        self.acc = accel_data
        self.gyr = gyros_data
        q: np.ndarray[float, Any] = self.quaternion

        # Normalise accelerometer measurement
        assert accel_data is not None
        assert gyros_data is not None

        # Gradient decent algorithm corrective step
        F: np.ndarray = np.array([2 * (q[1] * q[3] - q[0] * q[2]) - accel_data[0],
                                  2 * (q[0] * q[1] + q[2] * q[3]) -
                                  accel_data[1],
                                  2 * (0.5 - q[1] ** 2 - q[2] ** 2) - accel_data[2]])
      
        j1: list[float] = [-2 * q[2], 2 * q[3], -2 * q[0], 2 * q[1]]
        j2: list[float] = [2 * q[1], 2 * q[0], 2 * q[3], 2 * q[2]]
        j3 : list[float] = [0, -4 * q[1], -4 * q[2], 0]
        J: np.ndarray = np.array([j1, j2, j3])

        tolerance = 0.01
        step: np.ndarray = (J.T @ F).flatten()
        # normalise step magnitude
        step = - normalize(step, tolerance=tolerance)
        if np.linalg.norm(step) < 0.001:
            return
        # normalise step magnitude
        step = - step/np.linalg.norm(step)

        # Compute rate of change of quaternion
        qDot_omega = get_q_dot(q, gyros_data)
        self.qDot_omega = qDot_omega
        qDot: np.ndarray = qDot_omega + self.beta * step

        self.qDot = qDot

        dt = curr_time - self.prev_time
        # Integrate to yield quaternion
        q = quaternion_exponential_integration(
            q=q, omega_=qDot, dt=dt)
        norm = np.linalg.norm(q)
        if norm > 0.8 and norm < 1.2:
            self.quaternion = q/norm
        self.prev_time = curr_time
