import numpy as np
from Motor.libs.interface import CanBus
from Motor.libs.gyems import Gyems
import sys
import numpy as np
from RedisPostman.RedisWorker import AsyncRedisWorker


class CalibrationByAxis():
    """ Class used for calibration of a single axis. """


    g = 9.81

    def __init__(self, axis, n_measurements=1000, offsets_of_axis=[100000, 100000, 10000], to_show_progress=False) -> None:
        """
        :param axis: int, axis to calibrate
        :param n_measurements: int, number of measurements to take
        :param offsets_of_axis: list of ints, initial offsets for each axis
        :param to_show_progress: bool, whether to show progress during calibration
        """
        self.axis = axis
        self.coeff = 1
        self.mean_val = 0
        self.array: list[list[float]] = []
        self.n_measurements = n_measurements
        self.i = 0
        self.offsets_of_axis = offsets_of_axis
        self.to_show_progress = to_show_progress
        self.point = n_measurements/100
        self.increment = n_measurements/10

    def show_progress(self):
        """
        Function to show progress during calibration.
        """
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("\r[" + "=" * int(self.i / self.increment) + " " * int(
            (self.n_measurements - self.i) / self.increment) + "]" + str(self.i / self.point) + "%")
        sys.stdout.flush()

    def update(self, xyz):
        """
        Function to update calibration with new data.
        :param xyz: list of floats, data to update calibration with
        :return: int, 0 if calibration is not complete, 1 if calibration is complete
        """
        if self.to_show_progress:
            self.show_progress()
        if self.i < self.n_measurements:
            self.array.append(xyz)
            self.i += 1
            # n iterations less that the desired one
            return 0

        elif self.i == self.n_measurements:
            mean_val = self.g/(np.mean(self.array[self.axis]) -
                             self.offsets_of_axis[self.axis])
            self.coeff = mean_val

            array = np.array(self.array)

            i = 0
            while (i < 3):
                if i != self.axis:
                    mean_i = abs(np.mean(array[:, i], axis=0))
                    # changes > to < and made default offset != 0, 0, 0
                    if mean_i < abs(self.offsets_of_axis[i]):
                        self.offsets_of_axis[i] = np.mean(array[:, i], axis=0)
                i += 1
            # calibration complete
            return 1


class Calibration():
    """
    Abstract class which can be used for calibration
    """

    def __init__(self, n_measurements=1000) -> None:
        """
        :param n_measurements: int, number of measurements to take
        """
        self.axes = ["x", "y", "z"]
        self.n_measurements = n_measurements
        self.offsets = [0, 0, 0]

        self.gyr_calib_complete = False
        self.axis = 0
        self.current_axis = CalibrationByAxis(0)
        self.calib_axes: list[CalibrationByAxis] = []
        self.calibration_is_finished = False
        self.first_stage_of_calib_is_finished = False

    def update_axis(self):
        """
        Function to update current axis during calibration.
        """
        self.offsets = self.current_axis.offsets_of_axis
        self.current_axis = self.calib_axes[self.axis]

    def calibrate(self, xyz):
        """
        Function to set new data and get calibration parameters for each axis.
        :param xyz: list of floats, data to update calibration with
        :return: int, 0 if calibration is not complete, 1 if calibration is complete
        """
        result = self.current_axis.update(xyz)
        if result:  # calibration around axis is comlete
            self.update_axis()
            self.offsets = self.current_axis.offsets_of_axis
            self.axis += 1
            if self.calibration_is_finished:
                return 1
            return 0  # the calibration around one axis is comlete, change the axis


class CalibrationAcc(Calibration):
    """ Class used for accelerometer calibration. """
    def __init__(self, n_measurements=1000, to_show_progress=False) -> None:
        """
    :param n_measurements: int, number of measurements to take
    :param to_show_progress: bool, whether to show progress during calibration
    """
        super().__init__(n_measurements=n_measurements)
        self.acc_calib_x = CalibrationByAxis(
            axis=0, n_measurements=n_measurements, to_show_progress=to_show_progress, offsets_of_axis=[0, 10000, 10000])
        self.acc_calib_y = CalibrationByAxis(
            axis=1, n_measurements=n_measurements, to_show_progress=to_show_progress)
        self.acc_calib_z = CalibrationByAxis(
            axis=2, n_measurements=n_measurements, to_show_progress=to_show_progress)

        self.__to_show_progress__ = to_show_progress

        self.calib_axes = [self.acc_calib_x,
                           self.acc_calib_y, self.acc_calib_z]
        self.axis = 0
        self.current_axis = self.acc_calib_x

        print(
            f"\nPress ENTER to start calibrate accelerometer around the {self.axes[self.axis]} axis")
        input()

    def update_axis(self):
        """
        Function to update current axis during calibration.
        """
        if self.axis == 3:
            self.axis = 0
            print("x coeff", self.calib_axes[self.axis].coeff)
            self.calib_axes[self.axis].coeff -= self.offsets[0]
            print("x coeff", self.calib_axes[self.axis].coeff)
            # self.first_stage_of_calib_is_finished = True
            self.calibration_is_finished = True

            print("offsets", self.offsets)
        else:
            return super().update_axis()

    def calibrate(self, xyz):
        """
        Function to set new data and get calibration parameters for each axis.
        :param xyz: list of floats, data to update calibration with
        """
        result = super().calibrate(xyz)
        if result == 0:
            print("coeff", self.current_axis.coeff)
            if self.update_axis() != 1:
                self.current_axis.offsets_of_axis = self.offsets
                print(
                    f"\nRotate the IMU such as gravity is collinear with {self.axes[self.axis]}")
                print(
                    f"\nPress ENTER to start calibrate around the {self.axes[self.axis]} axis")
                input()
            self.current_axis.offsets_of_axis = self.offsets

    def get_coeffs(self):
        """
        Function to get calibration coefficients.
        :return: list of floats, calibration coefficients
        """
        coeffs = [axis.coeff for axis in self.calib_axes]
        return coeffs

    def get_offsets(self):
        """
        Function to get calibration offsets.
        :return: list of floats, calibration offsets
        """
        return self.offsets