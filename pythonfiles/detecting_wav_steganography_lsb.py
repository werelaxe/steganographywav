import data_steg
import wav_file
import steganography
from itertools import product


def brute_force_mask(in_wav_filename,
                     max_attempts_count,
                     mask_len=None,
                     buffer_size=100,
                     printing=False):
    if mask_len is not None:
        for row_mask in product('10', repeat=mask_len):
            mask = ''.join(row_mask)
            data_len = int(data_steg.get_storage_size(in_wav_filename, mask))
            in_wav = wav_file.WavFile(in_wav_filename)
            attempts_count = 0
            for e in range(data_len // buffer_size):
                data_buff = data_steg.read_data(in_wav, buffer_size, mask)
                try:
                    data = data_buff.decode()
                    format_str = 'mask = {}, result buffer: {}'
                    print(format_str.format(mask, repr(data)))
                except UnicodeDecodeError:
                    attempts_count += 1
                    if attempts_count >= max_attempts_count:
                        break
                if printing:
                    print(data_buff)
        return -1
    else:
        mask_len = 1
        while True:
            mask = brute_force_mask(
                in_wav_filename, max_attempts_count, mask_len=mask_len,
                buffer_size=buffer_size, printing=printing)
            if mask != -1:
                return mask
            else:
                mask_len += 1


def main():
    steganography.write_files('..\\wav files\\1 0.wav',
                              'out.wav',
                              ['..\\text files\\test_file.txt'],
                              False,
                              mask='1001')
    print('mask =', brute_force_mask('out.wav', 100, printing=False))


if __name__ == '__main__':
    main()
