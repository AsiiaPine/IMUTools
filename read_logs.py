from RedisPostman.RedisWorker import AsyncRedisWorker
import asyncio
from RedisPostman.models import LogMessage
from config import log_message_channel

async def main():
    in_channel_name = log_message_channel
    worker = AsyncRedisWorker()
    async for message in worker.subscribe(count=10000, block=1, dataClass=LogMessage, channel=in_channel_name):
        if message is None:
            continue
        try:
                assert isinstance(message, LogMessage)
                print(message)
        except KeyboardInterrupt:
            # await worker.broker.redis_client.delete(in_channel_name)
            return
        

if __name__ == "__main__":
    asyncio.run(main())
