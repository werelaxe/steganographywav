import argparse


def get_parser():
    parser = argparse.ArgumentParser(description='Wav steganography')

    parser.add_argument('-i', action='store',
                        dest='input', required=True,
                        help='input wav filename')

    parser.add_argument('-c', action='store_true', dest='compress',
                        help='write/read information with compressing')

    parser.add_argument('-g', action='store_true',
                        dest='listing',
                        help='print list of files in input wav file')

    parser.add_argument('-s', action='store_true', dest='storage',
                        help='print size of storage in wav file')

    subparsers = parser.add_subparsers(help="sub-command help")
    parser_write = subparsers.add_parser("write", help='write files')
    parser_read = subparsers.add_parser("read", help='read files')

    parser_write.add_argument('-f', action='store',
                        dest='files', required=True,
                        help='list of comma-separated files for writing')
    parser_write.add_argument('-o', action='store',
                        dest='output', default='out.wav',
                        help='output wav filename')

    parser_write.add_argument('-w', action='store_true',
                        help='no warnings with same input/output files',
                        dest='nowarnings')

    parser.add_argument('-d', action='store', dest='outdir',
                        help='out directory for unpacking files',
                        default='../unpack_dir')

    parser_read.add_argument('-r', action='store_true', dest='read',
                        help='reading files from '
                             'input wav to output directory', default=True)

    passw_and_mask = parser.add_mutually_exclusive_group()

    passw_and_mask.add_argument('-m', action='store', dest='mask',
                                help='mask which will be used'
                                     ' for writing or reading files',
                                default='1')
    passw_and_mask.add_argument('-p', action='store', dest='password',
                                help='password for '
                                     'encoding(used to create mask)',
                                default=None)
    parser_write.add_argument('-n', action='store_true', dest='noise',
                        help='add noises instead of zeros in mask')
    parser.add_argument('-l', action='store_true',
                        help='logging on', dest='loggingon')
    return parser
