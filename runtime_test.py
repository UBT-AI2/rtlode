from typing import List

from common import data_desc
from utils import num

_current_input_id = 0
_input_buffer = [None for _ in range(4096)]


def add_input(x_start: float, y_start: List[float], h: float, n: int) -> int:
    global _current_input_id

    system_size = 1

    input_desc = data_desc.get_input_desc(system_size)
    input_data = input_desc.create_write_instance()

    input_data.x_start.next = num.from_float(x_start)
    assert len(y_start) == system_size
    for i in range(system_size):
        input_data.y_start[i].next = num.from_float(y_start[i])
    input_data.h.next = num.from_float(h)
    input_data.n.next = int(n)

    _current_input_id = _current_input_id + 1
    input_data.id.next = int(_current_input_id)

    input_data.update()

    input_packed = input_data.packed()
    print('%r' % input_packed)
    assert (len(input_desc) / 8).is_integer()
    input_bytes = int(input_packed).to_bytes(int(len(input_desc) / 8), byteorder='little')
    for bi, b in enumerate(input_bytes):
        _input_buffer[bi] = b

    for i, val in enumerate(_input_buffer[0:int(len(input_desc) / 8)]):
        print('y_start[%s] = %s' % (i, val))

    return _current_input_id


if __name__ == '__main__':
    add_input(0, [2], 0.1, 20)
