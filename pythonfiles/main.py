import os
import sys
import hashlib
import parse_arguments
import steganography
import data_steg
import wav_file
from steganography_exceptions import DecodingError, WavFileError,\
    TooLargeDataError


def process_password(password):
    hash_tool = hashlib.md5()
    hash_tool.update(password.encode())
    hash_bytes = hash_tool.digest()[-8:]
    return ''.join(map(lambda x: bin(x)[2:].zfill(8), hash_bytes))


def process_storage(storage, in_filename, mask):
    if storage:
        with open(in_filename, 'rb') as in_file:
            print(steganography.get_storage_size(in_file, mask))


def process_listing(listing, in_filename, mask, compress):
    if listing:
        with open(in_filename, 'rb') as in_file:
            print(steganography.get_listing(in_file, mask, compress=compress))


def writing_files(files, in_filename,
                  out_filename, noise, mask, compress, nowarnings):
    if files is not None:
        old_out_filename = ''
        if (in_filename == out_filename) and not nowarnings:
            print("Input and output files are same. "
                  "Do you want to continue? [y/n]")
            if input() != 'y':
                sys.exit(0)
        same_io = in_filename == out_filename
        if same_io:
            old_out_filename = out_filename
            out_filename = 'tmp.wav'
        try:
            os.remove(out_filename)
        except FileNotFoundError:
            pass
        file_list = map(lambda x: open(x, 'rb'), files)
        with open(in_filename, 'rb') as in_file, \
                open(out_filename, 'ab') as out_file:
            steganography.write_files(
                in_file, out_file, file_list,
                noise, mask, compress=compress)
        if same_io:
            os.rename('tmp.wav', old_out_filename)


def reading_files(reading, in_filename, outdir, mask, compress):
    if reading:
        try:
            with open(in_filename, 'rb') as in_file:
                steganography.read_files(
                    in_file, outdir, mask, compress=compress)
        except DecodingError:
            print("Parsing error, try change mask or compression")
            sys.exit(0)


def main():
    out_filename = None
    nowarnings = None
    noise = None
    parser = parse_arguments.get_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = vars(parser.parse_args(sys.argv[1:]))
    # return
    in_filename = args['input']

    compress = args['compress']
    password = args['password']
    storage = args['storage']
    listing = args['listing']
    loggingon = args['loggingon']
    mask = args['mask']
    if 'files' in args:
        files = args['files']
    else:
        files = None
    if files is not None:
        files = args['files'].split(',')
        for file in files:
            if not os.path.exists(file):
                print('Sorry, but input binary '
                      'file {} doesn\'t exist'.format(file))
                sys.exit(2)
        nowarnings = args['nowarnings']
        out_filename = args['output']
        noise = args['noise']
    else:
        files = None
    outdir = args['outdir']
    if not os.path.exists(outdir):
        print('Sorry, but output directory {} doesn\'t exist'.format(outdir))
        sys.exit(2)

    if 'read' in args:
        reading = args['read']
    else:
        reading = False

    steganography.initialize_steganography(loggingon)
    wav_file.initialize_wav_file(loggingon)
    data_steg.initialize_data_steg(loggingon)
    if password is not None:
        mask = process_password(password)
    try:
        process_storage(storage, in_filename, mask)
        process_listing(listing, in_filename, mask, compress)
        writing_files(files, in_filename, out_filename,
                      noise, mask, compress, nowarnings)
        reading_files(reading, in_filename, outdir, mask, compress)

    except WavFileError:
        print("Unsupported file format")

    except TooLargeDataError:
        print("Too large files to write")
    except DecodingError:
        print("Decodin error, try change mask or password")
        sys.exit(2)

if __name__ == '__main__':
    main()
