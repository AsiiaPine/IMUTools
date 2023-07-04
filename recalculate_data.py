import asyncio
import datetime
import traceback

import numpy as np
from RedisPostman.models import IMUCoefficients,  IMUMessage, LogMessage, Message
import json
from config import calib_data_filename, imu_raw_message_channel, imu_calibrated_message_channel, log_message_channel
from RedisPostman.RedisWorker import AsyncRedisWorker


async def to_filter(array: list[IMUMessage], message: IMUMessage):
    assert isinstance(message, IMUMessage)
    array.append(message)

    if len(array) == 20:
        assert isinstance(array[0], IMUMessage)
        message.imu_1.acc = np.mean([mes.imu_1.acc for mes in array], axis=0)
        message.imu_2.acc = np.mean([mes.imu_2.acc for mes in array], axis=0)
        message.imu_1.gyr = np.mean([mes.imu_1.gyr for mes in array], axis=0)
        message.imu_2.gyr = np.mean([mes.imu_2.gyr for mes in array], axis=0)
        array = array[1:]


async def apply_coeffs_to_imu_message(coefficients: IMUCoefficients, in_channel_name: str, out_channel_name: str, in_dataClass: type[Message]):

    imu_1_acc_coeffs = coefficients.imu_1_acc.coeffs
    imu_1_acc_offset = coefficients.imu_1_acc.offset
    imu_1_gyr_coeffs = coefficients.imu_1_gyr.coeffs
    imu_1_gyr_offset = coefficients.imu_1_gyr.offset

    imu_2_acc_coeffs = coefficients.imu_2_acc.coeffs
    imu_2_acc_offset = coefficients.imu_2_acc.offset
    imu_2_gyr_coeffs = coefficients.imu_2_gyr.coeffs
    imu_2_gyr_offset = coefficients.imu_2_gyr.offset

    worker = AsyncRedisWorker()

    async for message in worker.subscribe(count=10000000, block=1, dataClass=in_dataClass, channel=in_channel_name):
        if message is not None:
            try:
                # print("Im'here")
                message.imu_1.gyr = (message.imu_1.gyr -
                                     imu_1_gyr_offset) * imu_1_gyr_coeffs
                message.imu_1.acc = (message.imu_1.acc -
                                     imu_1_acc_offset) * imu_1_acc_coeffs
                # message.imu_1.acc = message.imu_1.acc / \
                #     np.linalg.norm(message.imu_1.acc)

                message.imu_2.gyr = (message.imu_2.gyr -
                                     imu_2_gyr_offset) * imu_2_gyr_coeffs
                message.imu_2.acc = (message.imu_2.acc -
                                     imu_2_acc_offset) * imu_2_acc_coeffs
                # message.imu_2.acc = message.imu_2.acc / \
                #     np.linalg.norm(message.imu_1.acc)

                await worker.broker.publish(channel=out_channel_name, message=json.dumps(message.to_dict()))

            except KeyboardInterrupt:
                await worker.broker.redis_client.delete(out_channel_name)
                return
            except Exception as e:
                error_message = LogMessage(date=datetime.datetime.now(), process_name="recalculate_data", status=LogMessage.exception_to_dict(e))
                await worker.broker.publish(log_message_channel, json.dumps(error_message.to_dict()))


if __name__ == "__main__":
    # redis_ = aioredis.from_url("redis://localhost:6379/0")
    # broker = ARedisMessageBroker(redis)

    filename = calib_data_filename

    coeff = IMUCoefficients.acc_from_file(filename)

    asyncio.run(apply_coeffs_to_imu_message(coefficients=coeff, in_channel_name=imu_raw_message_channel,
                out_channel_name=imu_calibrated_message_channel, in_dataClass=IMUMessage))
