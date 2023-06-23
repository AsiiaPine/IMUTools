from typing import Union, Tuple

# Types

LimitTypes = Union[float, int]


# Functions
def sign(value: LimitTypes) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def limiter(value: LimitTypes, gain: Union[LimitTypes, Tuple[LimitTypes, LimitTypes]]) -> LimitTypes:
    if isinstance(gain, tuple):
        if gain[0] <= value <= gain[1]:
            return value
        return gain[0] if sign(value) < 0 else gain[1]

    if abs(gain) >= abs(value) and gain >= 0:
        return value
    elif abs(gain) <= abs(value) and gain < 0:
        return value

    return sign(value) * abs(gain)


def decode_error(error_code: int) -> dict:
    codes = bin(error_code)[2:]
    codes = "0" * (8 - len(codes)) + codes

    return {
        "voltage": codes[0] == "0",  # "Low voltage protection"
        "temp": codes[3] == "0"  # "Over temperature protection"
    }
