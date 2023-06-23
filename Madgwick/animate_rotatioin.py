from scipy.special import logsumexp #type:ignore
import matplotlib.pyplot as plt #type:ignore
import numpy as np
from Madgwick.visualize import visualize_rotation
import math


# ////////////////////////
# generate rotation matrix

def z_rotation(theta):
    R = np.array([[np.cos(theta), -np.sin(theta), 0],
                  [np.sin(theta), np.cos(theta), 0],
                  [0, 0, 1]])
    return R


def y_rotation(theta):
    R = np.array([[np.cos(theta), 0, np.sin(theta)],
                  [0, 1, 0],
                  [-np.sin(theta), 0, np.cos(theta)]])
    return R


def x_rotation(theta):
    R = np.array([[1, 0, 0],
                  [0, np.cos(theta), -np.sin(theta)],
                  [0, np.sin(theta), np.cos(theta)]])
    return R


def quaternion_product(p, q):
    Q = np.array([[p[0], -p[1], -p[2], -p[3]],
                  [p[1], p[0], -p[3], p[2]],
                  [p[2], p[3], p[0], -p[1]],
                  [p[3], -p[2], p[1], p[0]]])
    return Q @ q


def rot_matrix_quaternion(q):
    R = np.array([[
                    q[0] ** 2 + q[1] ** 2 - q[2] ** 2 - q[3] ** 2, 
                    2 * (q[1] * q[2] - q[0] * q[3]),
                    2 * (q[1] * q[3] + q[0] * q[2])],
                  [ 2 * (q[1] * q[2] + q[0] * q[3]), 
                    q[0] ** 2 - q[1] ** 2 + q[2] ** 2 - q[3] ** 2,
                    2 * (q[2] * q[3] - q[0] * q[1])],
                  [ 2 * (q[1] * q[3] - q[0] * q[2]), 
                   2 * (q[2] * q[3] + q[0] * q[1]),
                   q[0] ** 2 - q[1] ** 2 - q[2] ** 2 + q[3] ** 2]])
    return R


def quaternion_rotation_by_vec(theta, vector):
    direction = vector[1:]  # direction along which we rotate
    u = direction / np.linalg.norm(direction)
    q = np.hstack([[np.cos(theta / 2)], u * np.sin(theta / 2)])
    return rot_matrix_quaternion(q)
    # q_conj = np.hstack([[np.cos(theta / 2)], -u * np.sin(theta / 2)])
    # vprime = quaternion_product(q, quaternion_product(v, q_conj))
    # return vprime[1:]



def normalize(v, tolerance=0.00001):
    mag2 = logsumexp([n * n for n in v])
    if abs(mag2 - 1.0) > tolerance:
        mag = np.sqrt(mag2)
        v = tuple(n / mag for n in v)
    return np.array(v)


def quaternion_x_rotation(theta):
    # v = np.hstack([[0], vector])
    direction = np.array([1, 0, 0])  # direction along which we rotate
    u = direction / np.linalg.norm(direction)
    q = np.hstack([[np.cos(theta / 2)], u * np.sin(theta / 2)])
    return rot_matrix_quaternion(q)
    # q_conj = np.hstack([[np.cos(theta / 2)], -u * np.sin(theta / 2)])
    # vprime = quaternion_product(q, quaternion_product(v, q_conj))
    # return vprime[1:]


def quaternion_y_rotation(theta):
    direction = np.array([0, 1, 0])  # direction along which we rotate
    u = direction / np.linalg.norm(direction)
    q = np.hstack([[np.cos(theta / 2)], u * np.sin(theta / 2)])
    return rot_matrix_quaternion(q)


def quaternion_z_rotation(theta):
    direction = np.array([0, 0, 1])  # direction along which we rotate
    u = direction / np.linalg.norm(direction)
    q = np.hstack([np.cos(theta / 2), u * np.sin(theta / 2)])
    return rot_matrix_quaternion(q)


def L(q_1, q_2):
    s_1 = q_1[0]
    s_2 = q_2[0]

    v_1 = q_1[1:]
    v_2 = q_2[1:]

    operator_s = s_1 * s_2 - v_1.T @ v_2
    operator_v = v_2 * s_1 + v_1 @ v_2 + s_2 * v_1
    return np.concatenate(operator_s, operator_v)


def H(q_1, q_2):
    s_1 = q_1[0]
    s_2 = q_2[0]

    v_1 = q_1[1:]
    v_2 = q_2[1:]

    operator_s = s_1 * s_2 - v_1.T @ v_2
    operator_v = v_2 * s_1 - v_1 @ v_2 + s_2 * v_1
    return np.concatenate(operator_s, operator_v)


def get_R(q):
    return np.array([[-q[1], -q[2], -q[3]],
                     [q[0], q[3], -q[2]],
                     [-q[3], q[0], q[1]],
                     [q[2], -q[1], q[0]]])


def calc_q_dot(q, omega, R=None):
    R = get_R(q)
    return R @ omega / 2


def skew_matrix_calc(omega):
    return np.array([[0, -omega[2], omega[1]],
                     [omega[2], 0, -omega[0]],
                     [-omega[1], omega[0], 0]])


def dot_Rot(omega, R):
    S = skew_matrix_calc(omega)
    return S @ R


def get_new_R(q, omega, R, dt):
    dot_R = dot_Rot(omega, R)
    R = R + dt * dot_R
    return R @ omega / 2, R


def make_rotation(N=1000, tf=5, theta_f=np.pi / 2, funct=z_rotation):
    """

    :param N: number of timestamps
    :param tf: final timestamp, start is set to zero
    :param theta_f: angle to rotate the system
    :param funct:
    :return:
    """
    t = np.linspace(0, tf, N)
    rm = np.zeros([N, 3, 3])
    omega = theta_f / tf
    theta = np.zeros(N)

    for k in range(N):
        theta[k] = omega * t[k]
        rm[k, :, :] = funct(theta[k])
    # animate the rotation matrix and two scalar stats

    stats = [['time', t],
             ['theta', theta]]

    visualize_rotation(rm,
                       stats=stats)


# make_rotation()

# def forward_Euler(q0, dq, params, N=1000, t=5, ):
#     dt = t / N
#     t_span = np.linspace(0, t, N)  # time span
#     I = np.eye(q0.shape[0])
#
#     # Initial condition
#     xf_n = np.zeros((4, N))  # Forward euler trajectory
#     xf_n[:, 0] = q0  # update the array of states with initial condition
#
#     # Implement Forward euler
#     for i in range(1, N):
#         xf_n[:, i] = xf_n[:, i - 1] + dq(xf_n[:, i - 1], params) * dt
#
#     return xf_n, t_span


def make_quaternion_integration(q0, omega, N=1000, t=5, to_animate=True, to_plot_results=False):
    """
    The function makes forward Euler integration of the quaternion with set angular velocity - omega and visualize the rotation.
    :param q0: initial quaternion
    :param omega: angular velocity of the rotation
    :param N: number of timestamps
    :param t: time end
    :return:
    """
    rm = np.zeros([N, 3, 3])
    q = q0
    rot_q, t_span = forward_Euler(q0, calc_q_dot, omega, N=N, t=t)
    theta = np.zeros(N)

    for k in range(t_span.shape[0]):
        theta[k] = rot_q[0, k]
        rm[k, :, :] = rot_matrix_quaternion(normalize(rot_q[:, k]))
    anim = None
    fig, axs = None, None
    if to_animate:
        # animate the rotation matrix and two scalar stats

        stats = [['time', t_span],
                 ['theta', theta]]

        anim = visualize_rotation(rm,
                           stats=stats)
    if to_plot_results:
        norm = np.linalg.norm(rot_q, axis=0)
        fig, axs = plt.subplots(ncols=1, nrows=2, figsize=(18 * 2, 6 * 2))
        axs[0].title.set_text("Quaternions")
        axs[0].plot(t_span, rot_q[0, :], label="q_1")
        axs[0].plot(t_span, rot_q[1, :], label="q_2")
        axs[0].plot(t_span, rot_q[2, :], label="q_3")
        axs[0].plot(t_span, rot_q[3, :], label="q_4")
        axs[0].legend()
        axs[0].set_xlabel("t, s")
        axs[1].set_xlabel("t, s")

        axs[1].title.set_text("Quaternion norm dynamics")
        axs[1].plot(t_span, norm, label="norm")

        plt.legend()
        plt.show()
    return anim, fig, axs


def forward_Euler(q0, dq, params, N=1000, t=5, R0=None):
    dt = t / N
    t_span = np.linspace(0, t, N)  # time span
    # I = np.eye(q0.shape[0])

    # Initial condition
    xf_n = np.zeros((q0.shape[0], N))  # Forward euler trajectory
    xf_n[:, 0] = q0  # update the array of states with initial condition

    # Implement Forward euler
    for i in range(1, N):
        xf_n[:, i] = xf_n[:, i - 1] + dq(xf_n[:, i - 1], params) * dt

    return xf_n, t_span


def make_quaternion_integration_1(q0, omega, N=1000, t=5, R0=np.eye(3)):
    rm = np.zeros([N, 3, 3])
    q = q0

    rm, t_span = forward_Euler(R0, dot_Rot, omega, R0=R0, N=N, t=t)

    # animate the rotation matrix and two scalar stats

    stats = ['time', t_span]

    visualize_rotation(rm,
                       stats=stats)

# q_0 = np.array([1, 0, 0, 0]).T
# omega = np.array([0, 1, 0]).T
# make_quaternion_integration(q0=q_0, omega=omega)
# # make_quaternion_integration_1(q0=q_0, omega=omega, N=1000, t=5, R0=np.eye(3))
# make_rotation(funct=quaternion_z_rotation)
# make_rotation(funct=z_rotation)
