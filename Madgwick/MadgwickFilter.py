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

    def __init__(self, omega_e, sample_period=1 / 256, quaternion=None, beta: np.ndarray = np.ones(4), hpf=0, b: np.ndarray | None = None):
        if quaternion is None:
            quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
        self.prev_time: float = time.time()
        self.quaternion: np.ndarray = quaternion
        self.prev_quaternion: np.ndarray = quaternion
        if b is None:
            b = np.array([131, 94, 157])
        if beta is np.zeros(4):
            beta = np.sqrt(3)/2 * omega_e

        self.b = b
        self.beta: np.ndarray = beta
        self.hpf: float = hpf

        self.acc = np.zeros(3)
        self.gyr = np.zeros(3)

    def calc_objective_function_g(self, a: np.ndarray) -> np.ndarray:
        q_w: float
        q_x: float
        q_y: float
        q_z: float
        q_w, q_x, q_y, q_z = self.quaternion[0]
        F: np.ndarray = np.array([2 * (q_x * q_z - q_w * q_y) - a[0],
                                  2 * (q_w * q_x + q_y * q_z) -
                                  a[1],
                                  2 * (0.5 - q_x ** 2 - q_y ** 2) - a[2]])
        return F

    def calc_jacobian_g(self) -> np.ndarray:
        q_w: float
        q_x: float
        q_y: float
        q_z: float
        q_w, q_x, q_y, q_z = self.quaternion[0]
        j1: list[float] = [-2 * q_y, 2 * q_z, -2 * q_w, 2 * q_x]
        j2: list[float] = [2 * q_x, 2 * q_w, 2 * q_z, 2 * q_y]
        j3: list[float] = [0, -4 * q_x, -4 * q_y, 0]

        return np.array([j1, j2, j3])

    def calc_objective_function_b(self, m: np.ndarray) -> np.ndarray:
        b = self.b
        q_w: float
        q_x: float
        q_y: float
        q_z: float
        q_w, q_x, q_y, q_z = self.quaternion[0]
        f_b = np.array(
            [2*b[0](0.5 - q_y**2 - q_z**2) + 2*b[2]*(q_x*q_z - q_w*q_y) - m[0],
             2*b[0](q_y*q_x - q_w*q_z) + 2*b[2]*(q_w*q_x + q_y*q_z) - m[1],
             2*b[0]*(q_w*q_y + q_x*q_z) + 2*b[2](0.5 - q_x**2 - q_y**2) - m[2]])
        return f_b

    def calc_jacobian_b(self):
        b = self.b
        q_w: float
        q_x: float
        q_y: float
        q_z: float
        q_w, q_x, q_y, q_z = self.quaternion[0]

        j_1 = np.array(
            [-2*b[2] * q_y,       2*b[2]*q_z,               -4*b[0]*q_y - 2*b[2]*q_w,     -4*b[0]*q_z + 2 * b[2] * q_x])
        j_2 = np.array(
            [2*b[0]*(q_x - q_z),  2*b[0]*q_y + 2 * b[2]*q_w, 2*b[0] * q_x + 2*b[2] * q_z, -2*b[0]*q_w + 2*b[2]*q_y])
        j_3 = np.array(
            [2*b[0]*q_y,          2*b[0]*q_z - 4*b[2] * q_x, 2*b[0] * q_w - 4*b[2] * q_y,  2*b[0]*q_x])
        return np.array([j_1, j_2, j_3])

    def calc_step(self, F_g: np.ndarray, J_g: np.ndarray, F_b: np.ndarray | None = None, J_b: np.ndarray | None = None) -> np.ndarray:
        if F_b or J_b is None:
            return -1 * (J_g.T @ F_g).flatten()
        else:
            F_g_b = np.array([F_g, F_b])
            J_g_b = np.array([J_g.T, J_b.T])
            return -1*(J_g_b.T @ F_g_b).flatten()

    def update_IMU(self, gyros_data: np.ndarray, accel_data: np.ndarray, magn_data: np.ndarray | None = None):
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
        q_w: float = q[0]
        q_x: float = q[1]
        q_y: float = q[2]
        q_z: float = q[3]

        acc = accel_data/np.linalg.norm(accel_data)
        # Gradient decent algorithm corrective step
        F_g = self.calc_objective_function_g(acc)
        J_g = self.calc_jacobian_g()

        F_b = None
        J_b = None

        if magn_data is not None:
            F_b = self.calc_objective_function_b(magn_data)
            J_b = self.calc_jacobian_b()

        step = self.calc_step(F_g=F_g, F_b=F_b, J_b=J_b, J_g=J_g)

        tolerance = 0.01
        
        # normalize step magnitude
        # step = - normalize(step, tolerance=tolerance)
        if np.linalg.norm(step) < 0.001:
            return
        step = - step/np.linalg.norm(step)

        # Compute rate of change of quaternion
        qDot_omega = get_q_dot(q, gyros_data)
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