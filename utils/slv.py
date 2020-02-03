import json
import struct

FILE_NAME_ENDING = '.slv'
FILE_HEADER_IDENTIFIER = 'RTLODESLV'
FILE_HEADER_IDENTIFIER_LEN = len(FILE_HEADER_IDENTIFIER)


def _get_header(config):
    header = bytearray(FILE_HEADER_IDENTIFIER, encoding='ascii')
    header.extend(bytearray(list(struct.pack("<I", len(json.dumps(config))))))
    header.extend(bytearray(json.dumps(config), encoding='ascii'))
    return header


def pack(gbs_path, config, out_path):
    gbs = open(gbs_path, 'rb')
    gbs_content = gbs.read()

    slv_file_header = _get_header(config)
    with open(out_path, 'wb') as slv:
        slv.write(slv_file_header + gbs_content)


def unpack(slv_path, gbs_path=None):
    file = open(slv_path, 'rb')
    slv = file.read()

    if len(slv) < FILE_HEADER_IDENTIFIER_LEN \
            or slv[:FILE_HEADER_IDENTIFIER_LEN] != bytes(FILE_HEADER_IDENTIFIER, encoding='ascii'):
        raise Exception("Can't parse given slv file.")

    header_begin = FILE_HEADER_IDENTIFIER_LEN + 4
    header_len = struct.unpack("<I", slv[FILE_HEADER_IDENTIFIER_LEN:header_begin])[0]

    config = {}
    if header_len != 0:
        config = json.loads(slv[header_begin:(header_begin + header_len)])

    gbs_begin = header_begin + header_len
    if gbs_path is not None:
        if len(slv) <= gbs_begin:
            Exception("No gbs file embedded.")
        gbs_content = slv[gbs_begin:]

        with open(gbs_path, 'wb') as gbs:
            gbs.write(gbs_content)

    return config
