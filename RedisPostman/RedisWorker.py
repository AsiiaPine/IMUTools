import json
import traceback
from typing import Generator, AsyncGenerator
import redis
import numpy as np
from redis import asyncio as aioredis
from RedisPostman.models import IMUData, IMUMessage
from RedisPostman.models import Message
from RedisPostman.MessageBroker import ARedisMessageBroker, RedisMessageBroker


class AsyncRedisWorker:
    """
    AsyncRedisWorker is a class that provides an interface for subscribing 
    to Redis channels and receiving data in an asynchronous manner.

    Args: redis_db (aioredis.Redis):
        An instance of aioredis.
        Redis that represents the Redis database to connect to. 
        Defaults to aioredis.from_url("redis://localhost:6379/0").

    Methods: subscribe(dataClass, channel, block, count):
        An asynchronous method that subscribes 
        to a Redis channel and yields data as it is received.
    """

    def __init__(
            self,
            redis_db: aioredis.Redis = aioredis.from_url(
                "redis://localhost:6379/0"),
    ) -> None:
        self.r = redis_db
        self.broker = ARedisMessageBroker(redis_db)
        # By default, read from the last key. Skip old data.
        self.last_id = "$"

    async def subscribe(self, dataClass: type[Message], channel: str = "imu_data", block: int = 5, count=10000)->AsyncGenerator[None, Message]:
        """
        Args:
        dataClass: A class that represents the data being received. Must have a class method from_dict that takes a dictionary and returns an instance of the class.
        channel (str): The name of the Redis channel to subscribe to. Defaults to "imu_data".
        block (int): The number of seconds to block while waiting for new data. Defaults to 5.
        count (int): The maximum number of messages to retrieve at once. Defaults to 10000.

        Yields:
            An instance of dataClass representing the data received from the Redis channel.
        """
        async for last_id, messages in self.broker.subscribe_grouped(channel, self.last_id, block, count=count):
            # print(f"Got messages: {messages}")
            self.last_id = last_id
            if len(messages) > 0:
                last_message = messages[-1]
                try:
                    data = dataClass.from_dict(json.loads(last_message))
                    # print(f"Yielding data: {data}")
                    yield data
                except Exception as e:
                    print(e)
                    traceback.print_exc()

class RedisWorker:
    """
    A class for subscribing to Redis channels and reading data.

    Attributes:
    -----------
    r : redis.Redis
        A Redis client instance.
    broker : RedisMessageBroker
        An instance of the RedisMessageBroker class for subscribing to Redis channels.
    last_id : str
        The ID of the last message read from the Redis channel.

    Methods:
    --------
    subscribe(self, dataClass, channel: str = "imu_data", block: int = 5, count=10)
        Subscribe to a Redis channel and read data.

    """

    def __init__(
            self,
            redis_db: redis.Redis = redis.from_url("redis://localhost:6379/0"),
    ) -> None:
        """
        Initialize a RedisWorker instance.

        Parameters:
        -----------
        redis_db : redis.Redis
            A Redis client instance.
        """
        self.r = redis_db
        self.broker = RedisMessageBroker(redis_db)
        # By default, read from the last key. Skip old data.
        self.last_id = "$"

    def subscribe(self, dataClass: type[Message], channel: str = "imu_data", block: int = 5, count=10)->Generator[None, Message, None]:
        """
        Subscribe to a Redis channel and read data.

        Parameters:
        -----------
        dataClass : Type
            The class of the data to be read from the Redis channel.
        channel : str
            The name of the Redis channel to subscribe to.
        block : int
            The number of seconds to block while waiting for new messages.
        count : int
            The maximum number of messages to read at once.

        Yields:
        -------
        dataClass
            An instance of the dataClass class with the data read from the Redis channel.
        """
        for last_id, messages in self.broker.subscribe_grouped(channel, self.last_id, block, count=count):
            self.last_id = last_id
            if len(messages) > 0:
                last_message = messages[-1]
                data = dataClass.from_dict(json.loads(last_message))
                yield data
