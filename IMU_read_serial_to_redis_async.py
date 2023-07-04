import asyncio
import datetime
import serial  # type:ignore
import json
from redis import asyncio as aioredis
from RedisPostman.MessageBroker import ARedisMessageBroker
from config import headers, imu_raw_message_channel, log_message_channel
from RedisPostman.models import LogMessage


def open_serial_port():
    global serialPort
    serialPort = serial.Serial(
        port='/dev/ttyUSB0', baudrate=115200)  # open serial port
    print(serialPort.name)  # check which port was really used


async def read_serial_and_post_to_redis():
    """
    Read data from IMU using serial port and post to redis stream.
    """

    open_serial_port()
    serialString = serialPort.readline()
    print(serialString.decode('Ascii'))

    while (1):
        try:
            # Wait until there is data waiting in the serial buffer
            if (serialPort.in_waiting > 0):

                # Read data out of the buffer until a carraige return / new line is found
                serialString = serialPort.readline()

                # Get the contents of the serial data
                data = list(serialString.decode('Ascii').split(" "))

                # Build a dict with received data.
                result = {}
                for val, header in zip(data, headers):
                    result[header] = float(val)

                await broker.publish(imu_raw_message_channel, json.dumps(result))

        except KeyboardInterrupt:
            serialPort.close()
            await redis_.delete(imu_raw_message_channel)
            return

        except Exception as e:
            error_message = LogMessage(date=datetime.datetime.now(), process_name="IMU_read_serial_to_redis_async", status=LogMessage.exception_to_dict(e))
            message_str: str = json.dumps(error_message.to_dict())
            assert isinstance(message_str, str)
            await broker.publish(log_message_channel, message_str)
            serialPort.close()
            open_serial_port()


if __name__ == "__main__":

    redis_ = aioredis.from_url("redis://localhost:6379/0")
    broker = ARedisMessageBroker(redis_)

    serialPort: serial.Serial
    asyncio.run(read_serial_and_post_to_redis())
