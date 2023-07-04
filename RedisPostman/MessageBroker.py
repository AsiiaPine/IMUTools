import abc
from typing import AsyncIterator, Iterator
from redis import Redis
from redis.asyncio.client import Redis as aRedis


class MessageBroker(abc.ABC):
    """
    Abstract class for implementing message brokers.
    """
    @abc.abstractmethod
    def publish(self, channel: str, message: str):
        """
        Published the message to the specified channel.
        Operates on strings, so you need to serialize
        your data before publishing.

        JSON is a preferred format for serialization,
        since it is supported by all languages.
        """
        pass

    @abc.abstractmethod
    def subscribe(self, channel: str, last_id: str) -> Iterator[str]:
        """Subscribes to the specified channel and
        returns generator which yields messages."""
        pass


class AMessageBroker(abc.ABC):
    """
    Abstract class for implementing async message brokers.
    """


    @abc.abstractmethod
    async def publish(self, channel: str, message: str):
        """
        Published the message to the specified channel.
        Operates on strings, so you need to serialize
        your data before publishing.

        JSON is a preferred format for serialization,
        since it is supported by all languages.
        """
        pass
    
    
    @abc.abstractmethod
    async def subscribe(self, channel: str, last_id: str) -> AsyncIterator[tuple[str, str]]:
        """
        Asynchronously subscribes to the specified channel and
        returns async generator which yields messages.
        """
        pass
    

class RedisMessageBroker(MessageBroker):
    """
    Implementation of MessageBroker using Redis.

    Uses xadd/xread commands to publish/subscribe,
    plus allows to specify last_id to get new messages
    even after worker downtime.
    """

    redis_client: Redis

    def __init__(self, redis_pool: Redis) -> None:
        self.redis_client = redis_pool

    

    def publish(self, channel: str, message: str) -> None:
        self.redis_client.xadd(channel, {"message": message})


    def subscribe(
        self,
        channel: str,
        last_id: str,
    ) -> Iterator[tuple[str, str]]:
        """
        Subscribes to the specified channel and
        returns generator which yields messages.
        """
        if last_id:
            stream_id = last_id
        else:
            stream_id = "0"

        while True:
            # Continuosly poll for new messages,
            # sleeping for 1s if no messages are present.
            events = self.redis_client.xread(
                {channel: stream_id}, block=1000, count=10
            )
            print(f"Received events: {events}")
            for _, es in events:
                for e in es:
                    stream_id = e[0].decode()

                    if not b"message" in e[1].keys():
                        print("WARNING: Malfored message, skipping")
                        continue

                    message = e[1][b"message"].decode()
                    yield (stream_id, message)

    def subscribe_grouped(
        self,
        channel: str,
        last_id: str,
        block: int = 1000,
        count=10
    ) -> Iterator[tuple[str, list[str]]]:
        """
        Subscribes to the specified channel and
        returns Iterator which yields groups of messages
        that was sent during the entire period since last read.

        :channel: channel to subscribe to
        :last_id: last id of the message that was read
        :block: how long to wait for new messages before returning in ms
        """
        if last_id:
            stream_id = last_id
        else:
            stream_id = "0"

        while True:
            # Continuosly poll for new messages,
            # sleeping for 1s if no messages are present.
            events = self.redis_client.xread(
                {channel: stream_id}, block=block, count=count
            )
            result = []
            for _, es in events:
                for e in es:
                    stream_id = e[0].decode()
                    if not b"message" in e[1].keys():
                        print("WARNING: Malfored message, skipping")
                        continue
                    message = e[1][b"message"].decode()
                    result.append(message)

            # print(f"Yielding {stream_id}; {result}")
            yield (stream_id, result)


class ARedisMessageBroker(AMessageBroker):
    """
    Implementation of async MessageBroker using Redis.

    Uses xadd/xread commands to publish/subscribe,
    plus allows to specify last_id to get new messages
    even after worker downtime.
    """

    redis_client: aRedis

    def __init__(self, redis_pool: aRedis) -> None:
        self.redis_client = redis_pool

    

    async def publish(self, channel: str, message: str) -> None:
        await self.redis_client.xadd(channel, {"message": message})


    async def subscribe(
        self,
        channel: str,
        last_id: str,
    ) -> AsyncIterator[tuple[str, str]]:
        """
        Asynchronously subscribes to the specified channel and
        returns async generator which yields messages.
        """
        if last_id:
            stream_id = last_id
        else:
            stream_id = "0"

        while True:
            # Continuosly poll for new messages,
            # sleeping for 1s if no messages are present.
            events = await self.redis_client.xread(
                {channel: stream_id}, block=1000, count=10
            )
            for _, es in events:
                for e in es:
                    stream_id = e[0].decode()

                    if not b"message" in e[1].keys():
                        print("WARNING: Malformed message, skipping")
                        continue

                    message = e[1][b"message"].decode()
                    yield (stream_id, message)

    async def subscribe_grouped(
        self,
        channel: str,
        last_id: str,
        block: int = 5,
        count=10
    ) -> AsyncIterator[tuple[str, list[str]]]:
        """
        Asynchronously subscribes to the specified channel and
        returns async generator which yields groups of messages
        that was sent during the entire period since last read.

        :channel: channel to subscribe to
        :last_id: last id of the message that was read
        :block: how long to wait for new messages before returning in ms
        """
        if last_id:
            stream_id = last_id
        else:
            stream_id = "0"

        while True:
            # Continuosly poll for new messages,
            # sleeping for 1s if no messages are present.
            events = await self.redis_client.xread(
                {channel: stream_id}, block=block, count=count
            )
            result = []
            for _, es in events:
                for e in es:
                    stream_id = e[0].decode()

                    if not b"message" in e[1].keys():
                        print("WARNING: Malformed message, skipping")
                        continue

                    message = e[1][b"message"].decode()
                    result.append(message)

            yield (stream_id, result)
