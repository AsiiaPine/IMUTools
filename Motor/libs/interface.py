import os
import subprocess
from dataclasses import dataclass
from time import time
from typing import List

import can


@dataclass
class Response:
    id: int
    data: List[int]


class CanBus:

    def __init__(
        self,
        channel: str = "can0",
        bustype: str = "socketcan",
        baudrate: int = 115200,
        bitrate: int = 1000000
    ) -> None:
        self.port = subprocess.getoutput("ls /dev/ttyACM*")
        self.channel = channel
        self.bustype = bustype
        self.baudrate = baudrate
        self.bitrate = bitrate
        self.open()
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)

    def open(self) -> None:
        os.system(f'sudo slcand -o -c -s8 -S {self.baudrate} {self.port} {self.channel}')
        os.system(f'sudo ifconfig {self.channel} down')
        os.system(f'sudo ip link set {self.channel} type can bitrate {self.bitrate}')
        os.system(f'sudo ifconfig {self.channel} up')
        os.system(f'sudo ifconfig {self.channel} txqueuelen 65536')

    def close(self) -> None:
        os.system(f'sudo ifconfig {self.channel} down')

    def request(self, arbitration_id: int, data: List[int], timeout: float = 1, n_packets: int = 1) -> List[Response]:
        msg = can.Message(
            arbitration_id=arbitration_id,
            dlc=len(data),
            data=data
        )

        self.bus.send(msg)
        ans = []
        st_time = time()
        while True:
            if time() - st_time >= timeout:
                self.bus.send(msg)
                st_time = time()
            recv = self.bus.recv(0.1)

            if recv:
                ans.append(recv)

            if len(ans) == n_packets:
                break

        res = []
        for resp in ans:
            idx = resp.arbitration_id
            data = resp.data
            res.append(Response(idx, list(data)))
        return res

    def __del__(self) -> None:
        self.close()
