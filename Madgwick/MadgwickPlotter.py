"""
This code provides classes for plotting data from an IMU sensor using the Madgwick algorithm for attitude estimation.

The code includes two main classes: 
***MadgwickPlotter** and ***MadgwickPlotterFromAHRS***.

MadgwickPlotter 
It is a base class that provides methods for plotting data from an IMU sensor. 
It includes methods for plotting 3D rotations and 2D IMU data. 
The class takes in several parameters including:
- t_start which is the start time of the plot, 
- to_draw_3d which is a boolean indicating whether to plot 3D rotations or not, 
- to_draw_imu_data which is a boolean indicating whether to plot IMU data or not, 
- window_size which is the size of the window for plotting IMU data,
- imu_n which is the name of the IMU sensor.

MadgwickPlotterFromAHRS
It is a subclass of MadgwickPlotter that takes in an instance of the MadgwickAHRS class 
which provides the attitude estimation using the Madgwick algorithm. 
This class provides a method get_Madgwick_data which retrieves the attitude 
estimation data from the MadgwickAHRS instance and updates the data for plotting.

MadgwickRedisPlotter 
It is another subclass of MadgwickPlotter that is used for plotting data from a Redis database. 
It includes methods for updating the plot using data retrieved from the Redis database. 
The class takes in the same parameters as MadgwickPlotter.

Overall, this code provides a useful tool for visualizing data from an IMU sensor using the Madgwick algorithm for attitude estimation.
"""


from Madgwick.MadgwickFilter import MadgwickAHRS
from Madgwick.drawing import draw_rotation
from Madgwick.drawing import plot_imu_data
import matplotlib.pyplot as plt  # type:ignore
from matplotlib.axes import Axes  # type:ignore
import numpy as np
import time
import warnings


class MadgwickPlotter:
    def __init__(
        self,
            t_start: float = time.time(),
            to_draw_3d: bool = False,
            to_draw_imu_data: bool = False,
            window_size: int = 20,
            imu_n: str = "0",

    ) -> None:
        self.__gyr_array__ = np.zeros((2, 3))
        self.__acc_array__ = np.zeros((2, 3))

        self.time_window = [0.0, 0.0]
        self.acc = np.array([0, 0, 0])
        self.gyr = np.array([0, 0, 0])
        self.__window_size__ = window_size
        self.__start_time__ = t_start
        self.__prev_time__ = t_start
        self.quaternion = np.array([1,0,0,0])
        self.to_draw_3d = to_draw_3d
        self.to_draw_imu_data = to_draw_imu_data

        if to_draw_3d and to_draw_imu_data:
            warnings.warn(
                "Warning...........Dude, choose what to draw, not two in a time (((")
            to_draw_3d = False
            to_draw_imu_data = False

        if to_draw_3d:
            self.theta = 0
            self.fig = plt.figure()
            self.ax = self.fig.add_subplot(projection='3d')
            self.ax.axis('off')

        if to_draw_imu_data:
            self.i = 0
            self.imu_n = imu_n
            self.imu_axs, self.imu_fig = plot_imu_data(
                np.zeros((3, 3)), np.zeros((3, 3)), imu=imu_n, time=np.zeros(3)*t_start)

    def __plot_3d_view__(self):
        self.ax.clear()
        self.theta = self.quaternion[0]
        _, self.theta, _, _, _,  _, _ = draw_rotation(
            quaternion=self.quaternion, t=self.curr_time, fig=self.fig, ax=self.ax, theta=self.theta)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.0001)


    def __plot_2d_data__(self):
        for ax in self.imu_axs:
            ax.clear()
            assert isinstance(ax, Axes)
        if self.i > self.__window_size__:
            self.time_window = self.time_window[1:]
            self.__acc_array__ = self.__acc_array__[1:]
            self.__gyr_array__ = self.__gyr_array__[1:]
        self.__acc_array__ = np.vstack((self.__acc_array__, self.acc))
        self.__gyr_array__ = np.vstack((self.__gyr_array__, self.gyr))
        self.i += 1
        plot_imu_data(self.__acc_array__, self.__gyr_array__, imu=self.imu_n,
                      fig=self.imu_fig, axs=self.imu_axs, time=self.time_window)
        plt.pause(0.0001)

    def __update_plot__(self):
        self.curr_time = time.time() - self.__start_time__
        self.time_window.append(self.curr_time)
        if self.to_draw_3d:
            self.__plot_3d_view__()
        else:
            self.__plot_2d_data__()


class MadgwickPlotterFromAHRS(MadgwickPlotter):
    def __init__(self, madgwick: MadgwickAHRS, t_start: float = time.time(), to_draw_3d: bool = False, to_draw_imu_data: bool = False, window_size: int = 20, imu_n: str = "0") -> None:
        super().__init__(t_start, to_draw_3d, to_draw_imu_data, window_size, imu_n)
        self.madgwick = madgwick

    def get_Madgwick_data(self):
        if self.to_draw_imu_data:
            self.acc = self.madgwick.acc
            self.gyr = self.madgwick.gyr
        else:
            self.quaternion = self.madgwick.quaternion

    def update_plot(self):
        self.get_Madgwick_data()
        return super().__update_plot__()


class MadgwickRedisPlotter(MadgwickPlotter):
    def __init__(self, t_start: float = time.time(), to_draw_3d: bool = False, to_draw_imu_data: bool = False, window_size: int = 20, imu_n: str = "0") -> None:
        super().__init__(t_start, to_draw_3d, to_draw_imu_data, window_size, imu_n)

    def update_plot_from_redis(self, acc: np.ndarray = np.array([0, 0, 0]), gyr: np.ndarray = np.array([0, 0, 0]), quaternion: np.ndarray = np.array([1, 0, 0, 0])):
        if self.to_draw_imu_data:
            self.acc = acc
            self.gyr = gyr
        else:
            self.quaternion = quaternion

        return super().__update_plot__()