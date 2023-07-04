"""
The code can be used to proceed calibration of accelerometer data, all results will be stored in calib_data.json file.
If there already is some data, not related to the imus you want to calibrate, it will stay the same.
"""

from RedisPostman.RedisWorker import RedisWorker
import json
from AccelerometerCalibration.Calibration import CalibrationAcc
from config import acc_coefficients_str, acc_offsets_str, gyro_coefficients_str, gyro_offsets_str, imu_raw_message_channel, calib_data_filename
from RedisPostman.models import IMUCoefficients, IMUMessage

def main()->None:
    worker = RedisWorker()

    # Reading and storing data about calibration coeffitients from file with calib_data_filename
    f = open(calib_data_filename)
    calib_data_s: str = json.load(f)
    f.close()
    calib_data: dict = json.loads(calib_data_s)

    for imu_n in ["imu_1", "imu_2"]:
        if acc_coefficients_str not in calib_data[imu_n].keys():
            calib_data[imu_n][acc_coefficients_str] = [5000, 5000, 5000]
        if acc_offsets_str not in calib_data[imu_n].keys():
            calib_data[imu_n][acc_offsets_str] = [10000, 10000, 10000]
        if gyro_coefficients_str not in calib_data[imu_n].keys():
            calib_data[imu_n][gyro_coefficients_str] = [1, 1, 1]
        if gyro_offsets_str not in calib_data[imu_n].keys():
            calib_data[imu_n][gyro_offsets_str] = [10000, 10000, 10000]
    

    # First IMU calibration
    calibration_acc_1 = CalibrationAcc(
        n_measurements=1000, to_show_progress=True)
    for message in worker.subscribe(dataClass=IMUMessage, count=10000, channel=imu_raw_message_channel):
        if calibration_acc_1.calibration_is_finished:
            break
        if message is not None:
            calibration_acc_1.calibrate(message.imu_1.acc)

    print("\n_____\nNext IMU calibration starts!")

    # Second IMU calibration
    calibration_acc_2 = CalibrationAcc(
        n_measurements=1000, to_show_progress=True)
    for message in worker.subscribe(dataClass=IMUMessage, count=10000, channel=imu_raw_message_channel):
        if calibration_acc_2.calibration_is_finished:
            break
        if message is not None:
            calibration_acc_2.calibrate(message.imu_2.acc)

    print("\nCalibration complete")

    acc_offsets_1 = calibration_acc_1.get_offsets()
    acc_coefficients_1 = calibration_acc_1.get_coeffs()

    acc_offsets_2 = calibration_acc_2.get_offsets()
    acc_coefficients_2 = calibration_acc_2.get_coeffs()

    
    calib_data['imu_2'][acc_offsets_str] = acc_offsets_2
    calib_data['imu_2'][acc_coefficients_str] = acc_coefficients_2
    calib_data['imu_1'][acc_offsets_str] = acc_offsets_1
    calib_data['imu_1'][acc_coefficients_str] = acc_coefficients_1



    # calibr_results = {"imu_1":  {acc_offsets_str: acc_offsets_1, acc_coeffitients_str: acc_coefficients_1}, "imu_2": {
    #     acc_offsets_str: acc_offsets_2, acc_coeffitients_str: acc_coefficients_2}}
    calib_res_json = json.dumps(calib_data)

    with open('calib_data.json', 'w+', encoding='utf-8') as f:
        json.dump(calib_res_json, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    main()