import asyncio
from typing import Callable
from Madgwick.MadgwickPlotter import MadgwickRedisPlotter
from RedisPostman.models import Message
from RedisPostman.RedisWorker import AsyncRedisWorker
import numpy as np
from visualizer_options import options_names, options

async def visualize_imu(madgwick_plotter: MadgwickRedisPlotter, reader: Callable, channel: str, dataClass: type[Message]):
    """
    Generalized function for plotting the data from IMU, all possible options listed in reader_options.py
    """
    worker = AsyncRedisWorker()

    async for message in worker.subscribe(block=1, count=100000, dataClass=dataClass, channel=channel):
        if message is not None:
            result: dict[str, np.ndarray] = reader(message)
            madgwick_plotter.update_plot_from_redis(acc=result["acc"], gyr=result["gyr"], quaternion=result["quaternion"])

def print_dict(obj):
    s: str = ""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                s += k
                s += '\n'
                print_dict(v)
            else:
                s += '%s : \t%s\n' % (k, v)
    elif isinstance(obj, list):
        for v in obj:
            if hasattr(v, '__iter__'):
                print_dict(v)
            else:
                s += v
                s += '\t'
    else:
        s += obj
    return s

if __name__ == '__main__':

    available_options = {name: i for i, name in enumerate(list(options_names))}

    print("Choose an option:")
    print(print_dict(available_options))

    user_input = input()
    option_name = list(options_names)[int(user_input)]
    option = options[option_name]

    print(f"You've chosen {option_name}")

    assert isinstance(option["imu_name"], str)
    assert callable(option["reader"])
    assert isinstance(option["channel"], str)
    assert isinstance(option["dataClass"], type)
    assert issubclass(option["dataClass"], Message)
    assert isinstance(option['to_draw_imu_data'], bool)
    assert isinstance(option["to_draw_3d"], bool)
    madgwick_state = MadgwickRedisPlotter(
        to_draw_imu_data=bool(option['to_draw_imu_data']),
        to_draw_3d=bool(option["to_draw_3d"]),
        window_size=20,
        imu_n=option["imu_name"]
    )

    asyncio.run(visualize_imu(madgwick_plotter=madgwick_state, reader=option["reader"], channel=option["channel"], dataClass=option["dataClass"]))