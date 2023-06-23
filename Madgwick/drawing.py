from typing import Literal
import matplotlib.figure #type:ignore
import matplotlib.pyplot as plt #type:ignore
import numpy as np

from Madgwick.animate_rotatioin import normalize, rot_matrix_quaternion


def draw_rotation_in_time(rot_matrix, ax=None, fig=None, stats=None):

    axes_t = np.array([rot_matrix[:, 0],
                       rot_matrix[:, 1],
                       rot_matrix[:, 2]])
    if ax == None or fig == None:
        # Set up figure & 3D axis for animation
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.axis('off')
        print("ax was empty")

    # choose a different color for each trajectory
    colors = ['r', 'g', 'b']

    labels = ['x', 'y', 'z']

    # set up lines and points
    corner_text = ax.text(0.02, 0.90, 1.1, '')
    ax.set_xlim((-1.1, 1.1))
    ax.set_ylim((-1.1, 1.1))
    ax.set_zlim((-1.1, 1.1))
    ax.view_init(14, 0)

    stat_text: Literal[''] = ''
    if stats is not None:
        for stat in stats:
            stat_text += rf'{stat[0]}:  {round(stat[1], 3)}'
            stat_text += '\n'
            corner_text.set_text(stat_text)
    x, y, z = axes_t.T
    quiverx = ax.quiver(0, 0, 0, x[0], y[0], z[0],
                        color=colors[0], label=labels[0])
    quivery = ax.quiver(0, 0, 0, x[1], y[1], z[1],
                        color=colors[1], label=labels[1])
    quiverz = ax.quiver(0, 0, 0, x[2], y[2], z[2],
                        color=colors[2], label=labels[2])

    fig.canvas.draw()
    fig.canvas.flush_events()


def draw_rotation(
    quaternion: np.ndarray,
    ax: plt.Axes,
    fig: matplotlib.figure.Figure,
    theta=None,
    t=None,
):

    rm = rot_matrix_quaternion(normalize(quaternion))

    if theta is None:
        theta = np.arccos(rm[2, 2])
    else:
        theta = quaternion[0]

    if t is None:
        t = 0
    # choose a different color for each trajectory
    colors = ['r', 'g', 'b']
    labels = ['x', 'y', 'z']

    axes_t = np.array([rm[:, 0],
                       rm[:, 1],
                       rm[:, 2]])

    x, y, z = axes_t.T

    stats = [['time', t],
             ['theta', theta]]

    # Set up lines and points
    corner_text = ax.text2D(0.02, 0.90, '', transform=ax.transAxes)
    ax.set_xlim((-1.1, 1.1))
    ax.set_ylim((-1.1, 1.1))
    ax.set_zlim((-1.1, 1.1))
    ax.view_init(14, 0)

    stat_text = ''
    if stats is not None:
        for stat in stats:
            stat_text += rf'{stat[0]}:  {round(stat[1], 3)}'
            stat_text += '\n'
        corner_text.set_text(stat_text)

    quiverx = ax.quiver(X=[0], Y=[0], Z=[0],
                        U=x[0], V=y[0], W=z[0],
                        length=1, colors=colors[0], normalize=True, arrow_length_ratio=0.3, label=labels[0])
    quivery = ax.quiver(X=[0], Y=[0], Z=[0],
                        U=x[1], V=y[1], W=z[1],
                        length=1, colors=colors[1], normalize=True, arrow_length_ratio=0.3, label=labels[1])
    quiverz = ax.quiver(X=[0], Y=[0], Z=[0],
                        U=x[2], V=y[2], W=z[2],
                        length=1, colors=colors[2], normalize=True, arrow_length_ratio=0.3, label=labels[2])
    ax.legend()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return rm, theta, ax, fig, quiverx, quivery, quiverz


def plot_imu_data(accels, gyros, imu, axs=None, fig=None, time=None):
    N = max(accels.shape)
    
    if time is None:
        t_end = 10
        t_span = np.linspace(0, t_end, N)

    if type(time) is float:
        t_span = np.linspace(0, time, N)

    t_span = time
    if axs is None or fig is None:
        fig, axs = plt.subplots(ncols=1, nrows=2, figsize=(18 * 2, 6 * 2))
    linestyles: list[str] = ['solid', 'dashed', 'dotted', 'dashdot']

    axs[0].title.set_text(f"Acceleration {imu}")
    axs[0].plot(t_span, accels[:, 0], label="a_x", linestyle=linestyles[0])
    axs[0].plot(t_span, accels[:, 1], label="a_y", linestyle=linestyles[1])
    axs[0].plot(t_span, accels[:, 2], label="a_z", linestyle=linestyles[2])
    axs[0].set_xlabel("t, s")
    axs[0].set_ylabel("acceleration, rad/s^2")
    axs[0].legend()


    axs[1].title.set_text(f"Gyroscopes {imu}")
    axs[1].plot(t_span, gyros[:, 0], label="g_x", linestyle=linestyles[0])
    axs[1].plot(t_span, gyros[:, 1], label="g_y", linestyle=linestyles[1])
    axs[1].plot(t_span, gyros[:, 2], label="g_z", linestyle=linestyles[2])
    axs[1].set_xlabel("t, s")
    axs[1].set_ylabel("velocity, rad/s")
    axs[1].legend()

    fig.canvas.draw()
    fig.canvas.flush_events()
    return axs, fig