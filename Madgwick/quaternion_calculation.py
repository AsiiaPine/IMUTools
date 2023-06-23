import sys
from typing import Iterable
import numpy as np
from scipy.special import logsumexp #type:ignore


def normalize(v: Iterable, tolerance=0.001):
    mag2 = logsumexp([n * n for n in v])
    if abs(mag2 - 1.0) > tolerance:
        mag = np.sqrt(mag2)
        if mag == 0:
            # print("mag is less then 0:", mag)
            mag = sys.float_info.min
        v = [n / (mag) for n in v]
    return np.array(v)


# QUATERNIONS
def get_R(q) -> np.ndarray:
    """
    Matrix for quaternion product calculation. How to use?

    For two quaternions:
    q_1 mul q_2 = get_R(q_1) @ q_2

    For derivative:
    \dot_q = R(q) @ omega / 2
    :param q: 4x1 vector, a quaternion
    :return: 4x3 matrix R
    """
    
    return np.array([[-q[1], -q[2], -q[3]],
                     [q[0], q[3], -q[2]],
                     [-q[3], q[0], q[1]],
                     [q[2], -q[1], q[0]]])


def get_q_dot(q: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """
    Calculate derivative of the quaternion based on omega
    :param q: 4x1 vector, quaternion of the current state
    :param omega: 3x1 vector, angular velocity
    :return: 4x1 vector
    """
    R: np.ndarray = get_R(q)
    # print(f"R {R} ")
    # print(f"omega {omega} ")
    return R @ omega / 2


def multiply_quaternions(q_1: np.ndarray, q_2: np.ndarray) -> np.ndarray:
    """
    Quaternion product function
    :param q_1: 4x1 vector
    :param q_2: 4x1 vector
    :return: 4x1 vector, q_1 (x) q_2 result
    """
    scalar_part: float = q_1[0] * q_2[0] - np.dot(q_1[1:], q_2[1:])
    vector_part: np.ndarray = q_1[0] * q_2[1:] + q_2[0] * q_1[1:] + np.cross(q_1[1:], q_2[1:])

    return np.hstack([[scalar_part], vector_part])


def get_quaternion_exponential(omega_dt) -> np.ndarray:
    """
    The function calculates the quaternion exponential form (no need to normalize)
    :param omega_dt: just quaternion or the angle of rotation on one step (omega*dt)
    :return: normalized quaternion
    """

    omega = omega_dt[0]
    vector = omega_dt[1:]
    e_omega = np.e ** omega
    v_norm = np.linalg.norm(vector)
    w_exp = e_omega * np.cos(v_norm)
    v_exp = e_omega * np.sign(vector) * np.sin(v_norm)
    # e_v = np.cos(v_norm) + np.sign(vector) * np.sin(v_norm)
    return np.hstack((w_exp, v_exp))


def quaternion_exponential_integration(q, omega_, dt) -> np.ndarray:
    """
    The function calculates the quaternion on the next state
    :param q: q_i, current quaternion
    :param omega: omega_i, current angular velocity
    :param dt: timestep
    :return: q_{i+1}, next state quaternion
    """

    if max(omega_.shape) == 3:
        omega_ = np.hstack(([0.0], omega_))
    omega_hat = omega_
    exp: np.ndarray = get_quaternion_exponential(omega_hat * dt / 2)
    return multiply_quaternions(exp, q)


def quaternion_conj(q) -> np.ndarray:
    return np.array([q[0], -q[2] - q[3], -q[4]])
