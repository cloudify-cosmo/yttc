# Run converter from command line
import sys
import codecs
from yttc import convert


if __name__ == '__main__':
    filenames = sys.argv[1:]
    if not filenames:
        sys.stderr.write("No input files")
        sys.exit(1)
    fd = codecs.getwriter('utf8')(sys.stdout)
    convert(filenames, fd)
