# headers represent the order of IMU data in the Serial
headers = [

    "imu_1_gyr z",
    "imu_1_gyr y",
    "imu_1_gyr x",

    "imu_1_acc z",
    "imu_1_acc y",
    "imu_1_acc x",

    "imu_2_gyr z",
    "imu_2_gyr y",
    "imu_2_gyr x",

    "imu_2_acc z",
    "imu_2_acc y",
    "imu_2_acc x",
]

esp_headers=[
    "AcX", "AcY", "AcZ", "Tmp", "GyX", "GyY", "GyZ", "MaX", "MaY", "MaZ"
]

mpu9250_headers=[
    #TODO: ТУТ ХУЙНЯ КАКАЯ_ТО

    "imu_1_acc x",
    "imu_1_acc y",
    "imu_1_acc z",

    # "imu_1_tem",
    "imu_1_gyr x",
    "imu_1_gyr y",
    "imu_1_gyr z",

    "imu_1_mag x",
    "imu_1_mag y",
    "imu_1_mag z",

    "imu_2_mag z",
    "imu_2_mag y",
    "imu_2_mag x",

    "imu_2_gyr z",
    "imu_2_gyr y",
    "imu_2_gyr x",

    "imu_2_acc z",
    "imu_2_acc y",
    "imu_2_acc x",

    # "imu_2_tem",


    
]

# redis data channels names
imu_raw_message_channel = "imu_raw_data"
imu_calibrated_message_channel = "imu_calibrated_data"
madgwick_message_channel = "madgwick_data"

# logger stream name in redis database. Not is use for now. But it will be a great work.
log_message_channel = "logger"


# imu_names, which will be used in the redis database and plots
imu_1_name = "imu_1"
imu_2_name = "imu_2"

# name of file where all calibration coefficients are stored
calib_data_filename = "calib_data.json"

# names of calibration coefficients in the file with calib_data_filename
acc_offsets_str = "acc offsets"
acc_coefficients_str = "acc coeffs"

gyro_coefficients_str = "gyro coeffs"
gyro_offsets_str = "gyro offsets"

import numpy as np

# gyroscope parameters which has to be checked via experiments of from IMU documentation
# omega_e_imu_1 = [0.001, 0.006, 0.015]
# omega_e_imu_2 = [0.001, 0.01, 0.0075]

omega_e_imu_1 = [1, 1, 1]
omega_e_imu_2 = [0.01, 0.01, 0.01]