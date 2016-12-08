import unittest
from random import randint
from time import time


def calls_first_bin():
    for e in first_bin(randint(0, 255)):
        if e == '0':
            pass
        else:
            pass


def calls_second_bin():
    for e in second_bin(randint(0, 255)):
        if e == 0:
            pass
        else:
            pass


def first_bin(byte):
    return bin(byte)[2:].zfill(8)


def second_bin(byte):
    num = byte
    count = 0
    final = [0] * 8
    while num:
        final[7 - count] = num & 1
        num >>= 1
        count += 1
    final += [0] * (8 - count)
    return final


class Benchmark(unittest.TestCase):
    def test_methods(self):
        length = 100000
        start_time = time()
        for index in range(length):
            calls_first_bin()
        first_time = time()
        for index in range(length):
            calls_second_bin()
        second_time = time()
        print(first_time - start_time, second_time - first_time)
        self.assertTrue(first_time - start_time < second_time - first_time)
