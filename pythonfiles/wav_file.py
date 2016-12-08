from copy import copy
import logging
from steganography_exceptions import WavFileError, UnsupportedOperationError

PARAMS = ['chunk_id', 'chunk_size', 'format', 'subchunk1_id',
          'subchunk1_size', 'audio_format', 'num_channels',
          'sample_rate', 'byte_rate', 'block_align',
          'bits_per_sample', 'some_trash', 'subchunk2_id', 'subchunk2_size']

FDA = {(b'', b'd'): b'd', (b'd', b'a'): b'da',
       (b'da', b't'): b'dat', (b'dat', b'a'): b'data'}

CHUNK_ID = b'RIFF'
FORMAT = b'WAVE'
SUBCHUNK1_ID = b'fmt '
SUBCHUNK1_SIZE = 16
AUDIO_FORMAT = 1

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('stegano_logs.log')
fileHandler.setLevel(logging.DEBUG)
format_string = '%(name)s %(levelname)s %(asctime)s %(message)s'
formatter = logging.Formatter(format_string)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)


def initialize_wav_file(debug):
    global logger
    logger.disabled = not debug


def decode_int(data):
    return int.from_bytes(data, byteorder='little', signed=False)


def check_marks(file):
    chunk_id = file.read(4)
    if CHUNK_ID != chunk_id:
        logger.error('unsupported format file: {}'.format(chunk_id))
        raise WavFileError("unsupported format file: {}".format(chunk_id))
    params = decode_int(file.read(4))
    if FORMAT != file.read(4):
        logger.error('unsupported format file')
        raise WavFileError("unsupported format file")
    if SUBCHUNK1_ID != file.read(4):
        logger.error('unsupported format file')
        raise WavFileError("unsupported format file")
    subchunk_size = decode_int(file.read(4))
    if SUBCHUNK1_SIZE != subchunk_size:
        logger.error('unsupported format file')
        raise WavFileError("unsupported format file")
    audio_format = decode_int(file.read(2))
    if AUDIO_FORMAT != audio_format:
        logger.error('incorrect compress format')
        raise WavFileError("incorrect compress format")
    return params


class WavFile:
    def __init__(self, user_file, mode='r', params=None):
        logger.info('start logging in wavfile')
        self.mode = mode
        self.user_file = user_file
        if mode == 'r':
            self._read(user_file)
        elif mode == 'w':
            self._write(user_file, params)

    def _read(self, in_file):
        # in_file must be bytes-readable
        logger.info('start reading wav file')
        self.pointer = 0
        self.params = {}
        self.count_of_read_channels = 0

        self.params['chunk_size'] = check_marks(in_file)
        self.params['num_channels'] = decode_int(in_file.read(2))
        self.params['sample_rate'] = decode_int(in_file.read(4))
        self.params['byte_rate'] = decode_int(in_file.read(4))
        self.params['block_align'] = decode_int(in_file.read(2))
        self.params['bits_per_sample'] = decode_int(in_file.read(2))
        mark = in_file.read(4)
        if mark == b'data':
            self.some_trash = b''
        else:
            logger.warning('some trash in file was found')
            some_trash = bytearray(mark)
            state = b''
            while 1:
                c = in_file.read(1)
                if (state, c) in FDA.keys():
                        state = FDA[(state, c)]
                else:
                    state = b''
                if state == b'data':
                    self.subchunk2_id = b'data'
                    break
                else:
                    some_trash.append(c[0])
            self.some_trash = bytes(some_trash[:-3])
        self.params['some_trash'] = self.some_trash
        logger.info('some trash was successfully parsed')
        self.params['subchunk2_size'] = decode_int(in_file.read(4))
        self.head_size = 43 + len(self.some_trash)
        self.pointer = self.head_size + 1
        self.in_file = in_file

    def _write(self, out_file, params):
        logger.info('start writing in wav file')
        self.params = copy(params)
        data = [b'RIFF', params['chunk_size'].to_bytes(4, 'little'), b'WAVE',
                b'fmt ', SUBCHUNK1_SIZE.to_bytes(4, 'little'),
                AUDIO_FORMAT.to_bytes(2, 'little'),
                params['num_channels'].to_bytes(2, 'little'),
                params['sample_rate'].to_bytes(4, 'little'),
                params['byte_rate'].to_bytes(4, 'little'),
                params['block_align'].to_bytes(2, 'little'),
                params['bits_per_sample'].to_bytes(2, 'little'),
                params['some_trash'], b'data',
                params['subchunk2_size'].to_bytes(4, 'little')]
        out_file.write(b''.join(data))
        self.size = 43 + len(params['some_trash'])
        self.out_file = out_file

    def get_param(self, param):
        if param not in self.params.keys():
            raise KeyError('Parameter \"{}\" does not exist'.format(param))
        return self.params[param]

    def get_params(self):
        return self.params

    def get_channels_count(self):
        num_channels = self.params['num_channels']
        size = self.params['subchunk2_size']
        block_align = self.params['block_align']
        return num_channels * size // block_align

    def read_channels(self, count):
        if self.mode == 'w':
            raise UnsupportedOperationError(
                "Unsupported operation: not readable")
        self.in_file.seek(self.pointer)
        block_align = self.get_param('block_align')
        num_channels = self.get_param('num_channels')
        self.pointer += count * block_align // self.get_param('num_channels')
        channels = self.in_file.read(count * block_align // num_channels)
        self.count_of_read_channels += 1
        # logger.info('{} channel(s) was successfully read'.format(count))
        return channels

    def write_data(self, data):
        if self.mode == 'r':
            raise UnsupportedOperationError(
                "Unsupported operation: not readable")
        self.out_file.write(data)
        self.size += len(data)
        # logger.info('{} bytes was successfully wrote'.format(len(data)))

    def close(self):
        if self.mode == 'r':
            self.in_file.close()
        if self.mode == 'w':
            self.out_file.close()
        logger.info('wav file was successfully closed')

    def get_storage_size(self, mask):
        factor = sum(map(int, list(mask))) / len(mask)
        data_size = self.params['subchunk2_size']
        num_chan = self.params['num_channels']
        block_align = self.params['block_align']
        file_size = data_size * num_chan // block_align // 8
        return factor * file_size
