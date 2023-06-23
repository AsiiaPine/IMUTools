
# headers represent the order of IMU data in the Serial
headers = [

    "imu_1_gyro z",
    "imu_1_gyro y",
    "imu_1_gyro x",

    "imu_1_accel z",
    "imu_1_accel y",
    "imu_1_accel x",

    "imu_2_gyro z",
    "imu_2_gyro y",
    "imu_2_gyro x",

    "imu_2_accel z",
    "imu_2_accel y",
    "imu_2_accel x",
]

# redis data chennels names
imu_raw_message_channel = "imu_raw_data"
imu_calibrated_message_channel = "imu_calibrated_data"
madgwick_message_channel = "madgwick_data"

# logger stream name in redis database. Not is use for now. But it will be a great work.
log_message_channel = "logger"


# imu_names, which will be used in the redis database and plots
imu_1_name = "imu_1"
imu_2_name = "imu_2"

# name of file where all calibration coeffitients are stored
calib_data_filename = "calib_data.json"

# names of calibration coeffitients in the file with calib_data_filename
acc_offsets_str = "acc offsets"
acc_coefficients_str = "acc coeffs"

gyro_coefficients_str = "gyro coeffs"
gyro_offsets_str = "gyro offsets"

import numpy as np

# gyroscope parameters which has to be checked via experiments of from IMU documentation
omega_e_imu_1 = np.sqrt(3)/4
omega_e_imu_2 = np.sqrt(3)/4