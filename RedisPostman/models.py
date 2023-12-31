from dataclasses import dataclass
from typing import Any, Dict
from config import acc_coefficients_str, acc_offsets_str, gyro_coefficients_str, gyro_offsets_str, imu_1_name, imu_2_name
import numpy as np
import json
from datetime import datetime
import abc
import traceback


class Message(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> None:
        pass

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass


@dataclass
class IMUData:
    acc: np.ndarray
    gyr: np.ndarray

@dataclass
class IMU9250Data(IMUData):
    mag: np.ndarray

@dataclass
class IMUMessage(Message):
    imu_1: IMUData
    imu_2: IMUData

    @classmethod
    def from_dict(cls, data: dict[str, float]):
        """
        Deserialize message from JSON received from redis.
        """

        imu_1 = IMUData(
            acc=np.array([
                float(data["imu_1_acc x"]),
                float(data["imu_1_acc y"]),
                float(data["imu_1_acc z"]),
            ]),
            gyr=np.array([
                float(data["imu_1_gyr x"]),
                float(data["imu_1_gyr y"]),
                float(data["imu_1_gyr z"]),
            ]),
        )
        imu_2 = IMUData(
            acc=np.array([
                float(data["imu_2_acc x"]),
                float(data["imu_2_acc y"]),
                float(data["imu_2_acc z"]),
            ]),
            gyr=np.array([
                float(data["imu_2_gyr x"]),
                float(data["imu_2_gyr y"]),
                float(data["imu_2_gyr z"]),
            ]),
        )
        return cls(imu_1=imu_1, imu_2=imu_2)

    def to_dict(self):
        data = {}

        data["imu_1_acc x"] = self.imu_1.acc[0]
        data["imu_1_acc y"] = self.imu_1.acc[1]
        data["imu_1_acc z"] = self.imu_1.acc[2]

        data["imu_2_acc x"] = self.imu_2.acc[0]
        data["imu_2_acc y"] = self.imu_2.acc[1]
        data["imu_2_acc z"] = self.imu_2.acc[2]

        data["imu_1_gyr x"] = self.imu_1.gyr[0]
        data["imu_1_gyr y"] = self.imu_1.gyr[1]
        data["imu_1_gyr z"] = self.imu_1.gyr[2]

        data["imu_2_gyr x"] = self.imu_2.gyr[0]
        data["imu_2_gyr y"] = self.imu_2.gyr[1]
        data["imu_2_gyr z"] = self.imu_2.gyr[2]

        return data


@dataclass
class IMU9250Message(IMUMessage):
    imu_1 : IMU9250Data
    imu_2 : IMU9250Data

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """
        Deserialize message from JSON received from redis.
        """
        imu_d1 = data["imu_1"]
        imu_d2 = data["imu_2"]

        imu_1 = IMU9250Data(
            acc=np.array([
                float(imu_d1["AcX"]),
                float(imu_d1["AcY"]),
                float(imu_d1["AcZ"]),
            ]),
            gyr=np.array([
                float(imu_d1["GyX"]),
                float(imu_d1["GyY"]),
                float(imu_d1["GyZ"]),
            ]),
            mag=np.array([
                float(imu_d1["MaX"]),
                float(imu_d1["MaY"]),
                float(imu_d1["MaZ"])
            ]),
        )

        imu_2 = IMU9250Data(
            acc=np.array([
                float(imu_d2["AcX"]),
                float(imu_d2["AcY"]),
                float(imu_d2["AcZ"]),
            ]),
            gyr=np.array([
                float(imu_d2["GyX"]),
                float(imu_d2["GyY"]),
                float(imu_d2["GyZ"]),
            ]),
            mag=np.array([
                float(imu_d2["MaX"]),
                float(imu_d2["MaY"]),
                float(imu_d2["MaZ"])
            ]),
        )
        return cls(imu_1=imu_1, imu_2=imu_2)

    def to_dict(self):
        data = {"imu_1": {}, "imu_2": {}}

        data["imu_1"]["AcX"] = self.imu_1.acc[0]
        data["imu_1"]["AcY"] = self.imu_1.acc[1]
        data["imu_1"]["AcZ"] = self.imu_1.acc[2]

        data["imu_1"]["GyX"] = self.imu_1.gyr[0]
        data["imu_1"]["GyY"] = self.imu_1.gyr[1]
        data["imu_1"]["GyZ"] = self.imu_1.gyr[2]

        data["imu_1"]["MaX"] = self.imu_1.mag[0]
        data["imu_1"]["MaY"] = self.imu_1.mag[1]
        data["imu_1"]["MaZ"] = self.imu_1.mag[2]

        data["imu_2"]["AcX"] = self.imu_2.acc[0]
        data["imu_2"]["AcY"] = self.imu_2.acc[1]
        data["imu_2"]["AcZ"] = self.imu_2.acc[2]

        data["imu_2"]["GyX"] = self.imu_2.gyr[0]
        data["imu_2"]["GyY"] = self.imu_2.gyr[1]
        data["imu_2"]["GyZ"] = self.imu_2.gyr[2]

        data["imu_2"]["MaX"] = self.imu_2.mag[0]
        data["imu_2"]["MaY"] = self.imu_2.mag[1]
        data["imu_2"]["MaZ"] = self.imu_2.mag[2]
    
        return data


@dataclass
class Quaternion:
    value: np.ndarray


@dataclass
class MadgwickMessage(Message):
    imu_1: Quaternion
    imu_2: Quaternion

    @classmethod
    def from_dict(cls, data: dict[str, Any]):

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
class IMUCoefficients:
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
    def read_from_file(cls, coeff_dict_filename: str) -> "IMUCoefficients":
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
            print("gyr offsets:", calib_data[imu_n][gyro_offsets_str])
        imu_1_acc = IMUCalibrationData(offset=np.array(calib_data["imu_1"][acc_offsets_str]),
                                       coeffs=np.array(calib_data["imu_1"][acc_coefficients_str]))
        imu_2_acc = IMUCalibrationData(offset=np.array(calib_data["imu_2"][acc_offsets_str]),
                                       coeffs=np.array(calib_data["imu_2"][acc_coefficients_str]))
        imu_1_gyr = IMUCalibrationData(offset=np.array(calib_data["imu_1"][gyro_offsets_str]),
                                       coeffs=np.array(calib_data["imu_1"][gyro_coefficients_str]))
        imu_2_gyr = IMUCalibrationData(offset=np.array(calib_data["imu_2"][gyro_offsets_str]),
                                       coeffs=np.array(calib_data["imu_2"][gyro_coefficients_str]))
        return cls(imu_1_acc=imu_1_acc, imu_2_acc=imu_2_acc, imu_1_gyr=imu_1_gyr, imu_2_gyr=imu_2_gyr)


def dump_clean(obj, s="") -> str:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                s+= '\n'+ k + ':\n'
                s = dump_clean(v, s)
            else:
                s+= '%s : %s' % (k, v) + '\n'
    elif isinstance(obj, list):
        for v in obj:
            if hasattr(v, '__iter__'):
                s = dump_clean(v, s)
            else:
                s+= v + '\n'
    else:
        s+= obj + '\n'
    return s


@dataclass
class LogMessage(Message):
    date: datetime
    process_name: str
    status: dict[str, Any]

    date_format = '%m/%d/%Y\t%H:%M:%S'

    @staticmethod
    def exception_to_dict(exception: Exception) -> dict[str, Any]:
        exception_dict = {
            'type': type(exception).__name__,
            'message': str(exception),
            'args': str(exception.args),
            'traceback': traceback.format_exc()
        }
        return exception_dict

    @classmethod
    def from_dict(cls, data: dict[str, str | dict]):
        assert isinstance(data["process"], str)
        assert isinstance(data["date"], str)
        assert isinstance(data["status"], dict)

        process_name = data["process"]
        date_str_de_DE: str = data["date"]

        date: datetime = datetime.strptime(date_str_de_DE, cls.date_format)
        status: dict = data["status"]
        return cls(date=date, process_name=process_name, status=status)

    def to_dict(self) -> dict:
        data: dict[str, Any] = {}
        data["date"] = datetime.strftime(self.date, self.date_format)
        data["process"] = self.process_name
        data["status"] = self.status
        return data

    def __str__(self) -> str:
        return f'{self.date}\t{self.process_name}' + dump_clean(self.status)
