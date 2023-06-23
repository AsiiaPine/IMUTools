from typing import Callable
import numpy as np
from RedisPostman.models import IMUMessage, MadgwickMessage, Message
from config import imu_calibrated_message_channel, imu_raw_message_channel, madgwick_message_channel, imu_1_name, imu_2_name

def read_imu_1_data(message: IMUMessage) -> dict[str, np.ndarray]:
    return {"acc": message.imu_1.acc, "gyr": message.imu_1.gyr, "quaternion": np.zeros(4)}

def read_imu_2_data(message: IMUMessage) -> dict[str, np.ndarray]:
    return {"acc": message.imu_2.acc, "gyr": message.imu_2.gyr, "quaternion": np.zeros(4)}

def read_quaternion_1_data(message: MadgwickMessage) -> dict[str, np.ndarray]:
    return {"acc": np.zeros(3), "gyr": np.zeros(3), "quaternion": message.imu_1.value}

def read_quaternion_2_data(message: MadgwickMessage) -> dict[str, np.ndarray]:
    return {"acc": np.zeros(3), "gyr": np.zeros(3), "quaternion": message.imu_2.value}

options: dict[str, dict[str, bool| Callable | str | type[Message]]] = {
    "plot imu 1 raw data":
        {
            "to_draw_imu_data": True,
            "to_draw_3d": False,
            "channel": imu_raw_message_channel,
            "reader" : read_imu_1_data,
            "dataClass": IMUMessage,
            "imu_name": imu_1_name
        },
    "plot imu 2 raw data" : 
        {
            "to_draw_imu_data": True,
            "to_draw_3d": False,
            "channel": imu_raw_message_channel,
            "reader" : read_imu_2_data,
            "dataClass": IMUMessage,
            "imu_name": imu_2_name



        },
    "plot imu 1 calibrated data" : 
        {
            "to_draw_imu_data": True,
            "to_draw_3d": False,
            "channel": imu_calibrated_message_channel,
            "reader" : read_imu_1_data,
            "dataClass": IMUMessage,
            "imu_name": imu_1_name

        },

    "plot imu 2 calibrated data" : 
        {
            "to_draw_imu_data": True,
            "to_draw_3d": False,
            "channel": imu_calibrated_message_channel,
            "reader" : read_imu_2_data,
            "dataClass": IMUMessage,
            "imu_name": imu_2_name

        },
    
    "draw imu 1 madgwick results":
        {
            "to_draw_imu_data": False,
            "to_draw_3d": True,
            "channel": madgwick_message_channel,
            "reader" : read_quaternion_1_data,
            "dataClass": MadgwickMessage,
            "imu_name": imu_1_name
        },        
    "draw imu 2 madgwick results":
        {
            "to_draw_imu_data": False,
            "to_draw_3d": True,
            "channel": madgwick_message_channel,
            "reader" : read_quaternion_2_data,
            "dataClass": MadgwickMessage,
            "imu_name": imu_2_name
        },
}

options_names = options.keys()