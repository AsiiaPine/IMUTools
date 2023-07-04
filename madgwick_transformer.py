import asyncio
import datetime
from Madgwick.MadgwickFilter import MadgwickAHRS
from RedisPostman.models import IMUMessage, LogMessage
import json
from config import madgwick_message_channel,  imu_1_name, imu_2_name, imu_calibrated_message_channel, omega_e_imu_1, omega_e_imu_2, log_message_channel
from RedisPostman.RedisWorker import AsyncRedisWorker


async def transform_imu_data_to_quaternions(out_channel_name: str, in_channel_name:str):
    """
    Read data from IMU using serial port and post to redis stream.
    """
    mf1: MadgwickAHRS = MadgwickAHRS(omega_e=omega_e_imu_1)
    mf2: MadgwickAHRS = MadgwickAHRS(omega_e=omega_e_imu_2)

    worker = AsyncRedisWorker()

    async for message in worker.subscribe(count=10000000, block=1, dataClass=IMUMessage, channel=in_channel_name):
        if message is None:
            continue
        try:
            await mf1.async_update_IMU(gyros_data=message.imu_1.gyr,
                                accel_data=message.imu_1.acc)

            await mf2.async_update_IMU(gyros_data=message.imu_2.gyr,
                                accel_data=message.imu_2.acc)


            madgwick_data = {imu_1_name: mf1.quaternion.tolist(), imu_2_name: mf2.quaternion.tolist()}
            # print("[INFO]:\t", madgwick_data)

            await worker.broker.publish(channel=out_channel_name, message=json.dumps(madgwick_data))

        except KeyboardInterrupt:
            await worker.broker.redis_client.delete(madgwick_message_channel)
            return
        except Exception as e:
            error_message = LogMessage(date=datetime.datetime.now(), process_name="madgwick_transformer", status=LogMessage.exception_to_dict(e))
            await worker.broker.publish(log_message_channel, json.dumps(error_message.to_dict()))


if __name__ == "__main__":

    madgwick_data_channel = madgwick_message_channel

    asyncio.run(transform_imu_data_to_quaternions(in_channel_name=imu_calibrated_message_channel, out_channel_name=madgwick_data_channel))