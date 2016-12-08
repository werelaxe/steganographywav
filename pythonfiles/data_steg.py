import logging
from random import getrandbits
import itertools

from wav_file import WavFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('stegano_logs.log')
fileHandler.setLevel(logging.DEBUG)
format_string = '%(name)s %(levelname)s %(asctime)s %(message)s'
formatter = logging.Formatter(format_string)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)


def byte2bit(byte):
    return bin(byte)[2:].zfill(8)


def gen_mask(mask):
    for mask_cell in itertools.cycle(mask):
        yield mask_cell


def initialize_data_steg(debug):
    global logger
    logger.disabled = not debug


def set_zero_to_end(x):
    return x >> 1 << 1


def set_one_to_end(x):
    return x | 1


def randomizate_end(x):
    if bool(getrandbits(1)):
        return set_one_to_end(x)
    return set_zero_to_end(x)


def get_channels_left(in_wav_file, data_length):
    channels_count = in_wav_file.get_channels_count()
    block_align = in_wav_file.params['block_align']
    num_channels = in_wav_file.params['num_channels']
    writed_channels = data_length // block_align * num_channels
    channels_left = channels_count - writed_channels
    return channels_left


def write_data(in_wav_file, out_wav_file, in_data, noise, mask):
    mask_iterator = iter(gen_mask(mask))
    logger.info('start writing data with size = {}'.format(len(in_data)))
    out_file = out_wav_file
    for byte in in_data:
        bits = byte2bit(byte)
        for bit in bits:
            iswrote = False
            while not iswrote:
                channel = bytearray(in_wav_file.read_channels(1))
                if next(mask_iterator) == '1':
                    if bit == '0':
                        channel[0] = set_zero_to_end(channel[0])
                    else:
                        channel[0] = set_one_to_end(channel[0])
                    iswrote = True
                else:
                    if noise:
                        channel[0] = randomizate_end(channel[0])
                        iswrote = True
                out_file.write_data(bytes(channel))

    channels_left = get_channels_left(in_wav_file, len(in_data))
    out_file.write_data(in_wav_file.read_channels(channels_left))
    logger.info('writing {} bytes successfully complete'.format(len(in_data)))


def read_data(in_wav_file, data_length, mask, out_data=None):
    mask_iterator = iter(gen_mask(mask))
    for index in range(in_wav_file.count_of_read_channels % len(mask)):
        next(mask_iterator)
    logger.info('start writing data with size = {}'.format(data_length))
    buff = []
    final = bytearray()
    while len(final) < data_length:
        if next(mask_iterator) == '1':
            ch = in_wav_file.read_channels(1)
            buff.append(str(ch[0] % 2))
        else:
            in_wav_file.read_channels(1)
        if len(buff) == 8:
            num = int(''.join(buff), base=2)
            final.append(num)
            buff = []
    if out_data is None:
        return bytes(final)
    else:
        with open(out_data, 'wb') as file:
            file.write(bytes(final))
    format_str = 'writing {} bytes was successfully complete'
    logger.info(format_str.format(data_length))


def get_storage_size(in_file, mask):
    factor = sum(map(int, list(mask))) / len(mask)
    wav_file = WavFile(in_file)
    file_size = wav_file.get_storage_size(mask)
    return file_size * factor
