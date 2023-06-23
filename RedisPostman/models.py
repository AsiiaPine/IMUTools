from dataclasses import dataclass
from typing import Any
from config import acc_coefficients_str, acc_offsets_str, gyro_coefficients_str, gyro_offsets_str, imu_1_name, imu_2_name
import numpy as np
import json
from datetime import datetime
import abc


class Message(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: dict[str, str]) -> None:
        pass

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass
class IMUData:
    acc: np.ndarray
    gyr: np.ndarray


@dataclass
class IMUMessage(Message):
    imu_1: IMUData
    imu_2: IMUData

    @classmethod
    def from_dict(cls, data: dict[str, str]):
        """
        Deserialize message from JSON received from redis.
        """
        
        imu_1 = IMUData(
            acc=np.array([
                float(data["imu_1_accel x"]),
                float(data["imu_1_accel y"]),
                float(data["imu_1_accel z"]),
            ]),
            gyr=np.array([
                float(data["imu_1_gyro x"]),
                float(data["imu_1_gyro y"]),
                float(data["imu_1_gyro z"]),
            ]),
        )
        imu_2 = IMUData(
            acc=np.array([
                float(data["imu_2_accel x"]),
                float(data["imu_2_accel y"]),
                float(data["imu_2_accel z"]),
            ]),
            gyr=np.array([
                float(data["imu_2_gyro x"]),
                float(data["imu_2_gyro y"]),
                float(data["imu_2_gyro z"]),
            ]),
        )
        return cls(imu_1=imu_1, imu_2=imu_2)

    def to_dict(self):
        data = {}

        data["imu_1_accel x"] = self.imu_1.acc[0]
        data["imu_1_accel y"] = self.imu_1.acc[1]
        data["imu_1_accel z"] = self.imu_1.acc[2]

        data["imu_2_accel x"] = self.imu_2.acc[0]
        data["imu_2_accel y"] = self.imu_2.acc[1]
        data["imu_2_accel z"] = self.imu_2.acc[2]

        data["imu_1_gyro x"] = self.imu_1.gyr[0]
        data["imu_1_gyro y"] = self.imu_1.gyr[1]
        data["imu_1_gyro z"] = self.imu_1.gyr[2]

        data["imu_2_gyro x"] = self.imu_2.gyr[0]
        data["imu_2_gyro y"] = self.imu_2.gyr[1]
        data["imu_2_gyro z"] = self.imu_2.gyr[2]

        return data


@dataclass
class Quaternion:
    value: np.ndarray


@dataclass
class MadgwickMessage(Message):
    imu_1: Quaternion
    imu_2: Quaternion

    @classmethod
    def from_dict(cls, data: dict[str, str]):
        imu_1 = Quaternion(np.array([float(i)
                           for i in data[imu_1_name]]))
        imu_2 = Quaternion(np.array([float(i)
                           for i in data[imu_2_name]]))
        return cls(imu_1=imu_1, imu_2=imu_2)
    
    def to_dict(self) -> dict:
        raise Exception("Not implemented")


@dataclass
class IMUCalibrationData:
    offset: np.ndarray
    coeffs: np.ndarray


@dataclass
class IMUCoeffitients:
    """
    A class for loading IMU calibration coefficients from a file.

    Attributes:
    -----------
    imu_1_acc : IMUCalibrationData
        Calibration data for IMU 1 accelerometer.
    imu_1_gyr : IMUCalibrationData
        Calibration data for IMU 1 gyroscope.
    imu_2_acc : IMUCalibrationData
        Calibration data for IMU 2 accelerometer.
    imu_2_gyr : IMUCalibrationData
        Calibration data for IMU 2 gyroscope.

    Methods:
    --------
    acc_from_file(cls, coeff_dict_filename: str) -> "IMUCoeffitientsLoader":
        Class method to load calibration coefficients from a file and return an instance of the class.
    """

    imu_1_acc: IMUCalibrationData
    imu_1_gyr: IMUCalibrationData

    imu_2_acc: IMUCalibrationData
    imu_2_gyr: IMUCalibrationData

    @classmethod
    def acc_from_file(cls, coeff_dict_filename: str) -> "IMUCoeffitients":
        """
        Load calibration coefficients from a file and return an instance of the class.

        Parameters:
        -----------
        coeff_dict_filename : str
            The name of the file containing the calibration coefficients.

        Returns:
        --------
        IMUCoeffitientsLoader
            An instance of the class with the loaded calibration coefficients.
        """

        file = open(coeff_dict_filename)
        calib_data_s: str = json.load(file)
        file.close()

        calib_data: dict = json.loads(calib_data_s)
        for imu_n in ["imu_1", "imu_2"]:
            if acc_coefficients_str not in calib_data[imu_n].keys():
                calib_data[imu_n][acc_coefficients_str] = [1, 1, 1]
            if acc_offsets_str not in calib_data[imu_n].keys():
                calib_data[imu_n][acc_offsets_str] = [0, 10000, 10000]
            if gyro_coefficients_str not in calib_data[imu_n].keys():
                calib_data[imu_n][gyro_coefficients_str] = [1, 1, 1]
            if gyro_offsets_str not in calib_data[imu_n].keys():
                calib_data[imu_n][gyro_offsets_str] = [0, 0, 0]

        imu_1_acc = IMUCalibrationData(offset=np.array(calib_data["imu_1"][acc_offsets_str]),
                                       coeffs=np.array(calib_data["imu_1"][acc_coefficients_str]))
        imu_2_acc = IMUCalibrationData(offset=np.array(calib_data["imu_2"][acc_offsets_str]),
                                       coeffs=np.array(calib_data["imu_2"][acc_coefficients_str]))
        imu_1_gyr = IMUCalibrationData(offset=np.array(calib_data["imu_1"][gyro_offsets_str]),
                                       coeffs=np.array(calib_data["imu_1"][gyro_coefficients_str]))
        imu_2_gyr = IMUCalibrationData(offset=np.array(calib_data["imu_2"][gyro_offsets_str]),
                                       coeffs=np.array(calib_data["imu_2"][gyro_coefficients_str]))
        return cls(imu_1_acc=imu_1_acc, imu_2_acc=imu_2_acc, imu_1_gyr=imu_1_gyr, imu_2_gyr=imu_2_gyr)


def dumpclean(obj) -> str:
    s: str = ""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                s += k
                dumpclean(v)
            else:
                s += '%s : %s' % (k, v)
    elif isinstance(obj, list):
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                s += v
    else:
        s += obj
    return s


@dataclass
class LoggMessage(Message):
    date: datetime
    process_name: str
    status: dict[str, Any]

    @classmethod
    def create_log(cls, process_name: str, status: dict[str, Any]):
        return cls(date=datetime.now(), process_name=process_name, status=status)

    def __str__(self) -> str:
        return f'{self.date}\t{self.process_name}\t{dumpclean(self.status)}'
