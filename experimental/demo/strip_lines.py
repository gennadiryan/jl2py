import os
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fname = sys.argv[1]

        with open(fname, 'r') as f:
            for line in f.read().split('\n'):
                if line[:4] in ('>>> ', '... '):
                    print(line[4:])
