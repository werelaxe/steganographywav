import steganography
import os
import unittest
import random
import data_steg
import wav_file

IN_WAV_FILENAME = os.path.join('..', 'wav files', 'music.wav')
OUT_WAV_FILENAME = 'out.wav'
OUT_DIR = os.path.join('..', 'unpack_dir')
TEXT_FILENAME = os.path.join('..', 'files', 'textfile.txt')
OUT_TEXT_FILENAME = os.path.join('..', 'unpack_dir', 'textfile.txt')
PICTURE_FILENAME = os.path.join('..', 'files', 'python.jpg')
ARCHIVE_FILENAME = os.path.join('..', 'files', 'archive.rar')


def gen_random_mask(length):
    return ''.join([random.choice(['1', '0']) for e in range(length)])


def func_create_label(x):
    return os.path.basename(x.name), os.path.getsize(x.name)


class SteganographyTester(unittest.TestCase):
    compress = False
    try:
        os.remove(OUT_WAV_FILENAME)
    except FileNotFoundError:
        pass
    for filname in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, filname))

    def test_wav_opening(self):
        with open(IN_WAV_FILENAME, 'rb') as in_wav_file:
            with open(OUT_WAV_FILENAME, 'ab') as out_wav_file:
                in_file = wav_file.WavFile(in_wav_file)
                out_file = wav_file.WavFile(out_wav_file, 'w', in_file.params)
                hash(out_file)
        os.remove(OUT_WAV_FILENAME)

    def test_data_steg(self):
        with open(IN_WAV_FILENAME, 'rb') as in_file:
            with open(OUT_WAV_FILENAME, 'ab') as out_file:
                in_wav_file = wav_file.WavFile(in_file)
                out_wav_file = wav_file.WavFile(
                    out_file, 'w', params=in_wav_file.get_params())
                data = os.urandom(100)
                data_steg.write_data(
                    in_wav_file, out_wav_file, data, False, '1')
        with open(OUT_WAV_FILENAME, 'rb') as in_file:
            read_wav_file = wav_file.WavFile(in_file)
            self.assertEqual(data_steg.read_data(
                read_wav_file, mask='1', data_length=len(data)), data)
        os.remove(OUT_WAV_FILENAME)

    def test_size(self):
        with open(IN_WAV_FILENAME, 'rb') as in_file,\
                open(OUT_WAV_FILENAME, 'ab') as out_file,\
                open(TEXT_FILENAME, 'rb') as text_file:
            steganography.write_files(
                in_file, out_file, [text_file],
                False, compress=self.compress)
        expected_size = os.path.getsize(OUT_WAV_FILENAME)
        real_size = os.path.getsize(IN_WAV_FILENAME)
        self.assertEqual(expected_size, real_size)
        with open(OUT_WAV_FILENAME, 'rb') as read_file:
            steganography.read_files(
                read_file, OUT_DIR, compress=self.compress)
        expected_size = os.path.getsize(TEXT_FILENAME)
        real_size = os.path.getsize(OUT_TEXT_FILENAME)
        self.assertEqual(expected_size, real_size)
        os.remove(OUT_WAV_FILENAME)
        os.remove(OUT_TEXT_FILENAME)

    def test_equals(self):
        with open(IN_WAV_FILENAME, 'rb') as in_file,\
                open(OUT_WAV_FILENAME, 'ab') as out_file,\
                open(TEXT_FILENAME, 'rb') as text_file:
            steganography.write_files(
                in_file, out_file, [text_file],
                False, compress=self.compress)
        with open(OUT_WAV_FILENAME, 'rb') as read_file:
            steganography.read_files(
                read_file, OUT_DIR, compress=self.compress)
        with open(TEXT_FILENAME, 'rb') as expected_file:
            with open(OUT_TEXT_FILENAME, 'rb') as real_file:
                self.assertEqual(expected_file.read(), real_file.read())
        os.remove(OUT_WAV_FILENAME)
        os.remove(OUT_TEXT_FILENAME)

    def test_label(self):
        with open(TEXT_FILENAME, 'rb') as text_file,\
                open(PICTURE_FILENAME, 'rb') as picture_file,\
                open(ARCHIVE_FILENAME, 'rb') as arch_file,\
                open(IN_WAV_FILENAME, 'rb') as in_file,\
                open(OUT_WAV_FILENAME, 'ab') as out_file:
            file_list = [text_file, picture_file, arch_file]
            steganography.write_files(
                in_file, out_file, file_list,
                noise=False, compress=self.compress)
        with open(OUT_WAV_FILENAME, 'rb') as read_file:
            label = steganography.get_listing(
                read_file, compress=self.compress)
            real_label = list(map(func_create_label, file_list))
            self.assertEqual(label, real_label)
        os.remove(OUT_WAV_FILENAME)

    def test_mask(self):
        mask = gen_random_mask(4)
        with open(IN_WAV_FILENAME, 'rb') as in_file,\
                open(OUT_WAV_FILENAME, 'ab') as out_file,\
                open(TEXT_FILENAME, 'rb') as text_file:
            steganography.write_files(
                in_file, out_file, [text_file],
                False, compress=self.compress, mask=mask)
        with open(OUT_WAV_FILENAME, 'rb') as read_file:
            steganography.read_files(
                read_file, OUT_DIR, compress=self.compress, mask=mask)

        with open(TEXT_FILENAME, 'rb') as expected_file:
            with open(OUT_TEXT_FILENAME, 'rb') as real_file:
                self.assertEqual(expected_file.read(), real_file.read())
        os.remove(OUT_WAV_FILENAME)

    def test_data_steg_additivity(self):
        with open(IN_WAV_FILENAME, 'rb') as in_file, \
                open(OUT_WAV_FILENAME, 'ab') as out_file:
            in_wav_file = wav_file.WavFile(in_file)
            out_wav_file = wav_file.WavFile(
                out_file, 'w', params=in_wav_file.get_params())
            data = os.urandom(100)
            data_steg.write_data(in_wav_file, out_wav_file, data, False, '1')
        with open(OUT_WAV_FILENAME, 'rb') as read_file:
            read_wav_file = wav_file.WavFile(read_file)
            first_data = data_steg.read_data(read_wav_file,
                                             mask='1',
                                             data_length=len(data) // 2)
            second_data = data_steg.read_data(read_wav_file,
                                              mask='1',
                                              data_length=len(data) // 2)
            self.assertEqual(first_data + second_data, data)
        os.remove(OUT_WAV_FILENAME)


class SteganographyTesterWithCompression(SteganographyTester):
    compress = True
