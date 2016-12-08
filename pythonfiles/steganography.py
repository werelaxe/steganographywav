import logging
import os
import gzip
import data_steg
import pickle
from wav_file import WavFile
from steganography_exceptions import DecodingError, TooLargeDataError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('stegano_logs.log')
fileHandler.setLevel(logging.DEBUG)
format_string = '%(name)s %(levelname)s %(asctime)s %(message)s'
formatter = logging.Formatter(format_string)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)


def initialize_steganography(debug):
    global logger
    logger.disabled = not debug


def get_storage_size(in_file, mask='1'):
    size = data_steg.get_storage_size(in_file, mask)
    in_file.seek(0)
    return size


def make_mark(file_list):
    label = list(map(lambda x: (os.path.basename(x.name),
                                os.path.getsize(x.name)), file_list))
    mark = len(pickle.dumps(label)).to_bytes(1, 'little')
    mark += pickle.dumps(label)
    logger.info('mark was successfully created')
    return mark


def read_size(data):
    size = int.from_bytes(data, byteorder='little', signed=False)
    logger.info('size was successfully read')
    return size


def read_label(data):
    try:
        label = pickle.loads(data)
    except (pickle.UnpicklingError, ValueError, EOFError):
        raise DecodingError(
            "Error decoding, try change mask or input password")
    logger.info('label was successfully read')
    return label


def create_data(file_list):
    data = make_mark(file_list)
    for file in file_list:
        data += file.read()
    logger.info('data was successfully created')
    return data


def finalize_data(data):
    compressed_data = gzip.compress(data)
    len_of_compressed_data = (len(compressed_data)).to_bytes(27, 'little')
    final_data = len_of_compressed_data + compressed_data
    logger.info('data was successfully compressed and finalize')
    return final_data


def _write_files(in_file, out_file, files, noise, mask):
    format_str = 'start writing files {} without compression to {} with {}'
    logger.info(format_str.format(files, out_file.name, in_file.name))
    data = create_data(files)
    if len(data) > data_steg.get_storage_size(in_file, mask):
        logger.error('size of file more than size of storage')
        raise TooLargeDataError("Too large data")
    in_file.seek(0)
    in_wav_file = WavFile(in_file)
    out_wav_file = WavFile(out_file, mode='w',
                           params=in_wav_file.params)
    data_steg.write_data(in_wav_file, out_wav_file, data, noise, mask)

    format_str = 'writing files {} to {} with {} was successfully completed'
    logger.info(format_str.format(files, out_wav_file, in_wav_file))


def _write_files_with_compress(
        in_file, out_file, files, noise, mask):
    format_str = 'start writing files {} with compression to {} with {}'
    logger.info(format_str.format(files, out_file.name, in_file.name))
    data = finalize_data(create_data(files))
    if len(data) > data_steg.get_storage_size(in_file, mask):
        logger.error('size of file more than size of storage')
        raise TooLargeDataError("Too large data")
    in_file.seek(0)
    in_wav_file = WavFile(in_file)
    out_wav_file = WavFile(
        out_file, mode='w', params=in_wav_file.params)
    data_steg.write_data(in_wav_file, out_wav_file, data, noise, mask)
    format_str = 'writing files {} with compression to' \
                 '{} with {} was successfully completed'
    logger.info(format_str.format(files, out_wav_file, in_wav_file))


def _read_files_with_compress(in_file, out_dir, mask):
    format_str = 'start reading files with compression from {}'
    logger.info(format_str.format(in_file.name))

    in_wav_file = WavFile(in_file)

    size = read_size(data_steg.read_data(in_wav_file, 27, mask))
    compressed_data = data_steg.read_data(in_wav_file, size, mask)

    try:
        decompressed_data = gzip.decompress(compressed_data)
    except OSError:
        message_error = 'Error decoding, try change mask or input password'
        raise DecodingError(message_error)
    logger.info('data with size {} was successfully completed'.format(size))
    label_size = read_size(decompressed_data[0:1])
    label = read_label(decompressed_data[1:label_size + 1])
    pointer = label_size
    for name in label:
        data = decompressed_data[pointer + 1:pointer + name[1] + 1]
        pointer += name[1]
        with open(os.path.join(out_dir, name[0]), 'wb') as file:
            file.write(data)
    logger.info('reading files with compression'
                ' from {} was successfully completed'.format(in_file.name))


def _read_files(in_file, out_dir, mask):
    format_str = 'start reading files from {}'
    logger.info(format_str.format(in_file.name))
    in_wav_file = WavFile(in_file)
    size = read_size(data_steg.read_data(in_wav_file, 1, mask)[0:1])
    data_label = data_steg.read_data(in_wav_file, size, mask)
    label = read_label(data_label)
    for name in label:
        data = data_steg.read_data(in_wav_file, name[1], mask)
        with open(os.path.join(out_dir, name[0]), 'wb') as file:
            file.write(data)
    logger.info('reading files from {}'
                'was successfully completed'.format(in_file.name))


def read_files(in_file, out_dir, mask='1', compress=False):
    if compress:
        _read_files_with_compress(in_file, out_dir, mask)
    else:
        _read_files(in_file, out_dir, mask)


def write_files(
        in_file, out_file, files,
        noise, mask='1', compress=False):
    if compress:
        _write_files_with_compress(
            in_file, out_file, files, noise, mask)
    else:
        _write_files(
            in_file, out_file, files, noise, mask)


def _get_listing(in_file, mask):
    in_wav_file = WavFile(in_file)
    size = read_size(data_steg.read_data(in_wav_file, 1, mask)[0:1])
    label = read_label(data_steg.read_data(in_wav_file, size, mask))
    logger.info('listing was successfully completed')
    return label


def _get_listing_with_compression(in_file, mask):
    in_wav_file = WavFile(in_file)
    size = read_size(data_steg.read_data(in_wav_file, 27, mask))
    compressed_data = data_steg.read_data(in_wav_file, size, mask)
    decompressed_data = gzip.decompress(compressed_data)
    logger.info('data with size {} was successfully completed'.format(size))
    label_size = read_size(decompressed_data[0:1])
    label = read_label(decompressed_data[1:label_size + 1])
    logger.info('listing with compression was successfully completed')
    return label


def get_listing(in_file, mask='1', compress=False):
    if compress:
        return _get_listing_with_compression(in_file, mask)
    else:
        return _get_listing(in_file, mask)
