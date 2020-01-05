#!/usr/bin/env python

import sys

for line in sys.stdin.readlines():
    bird, country = line.rstrip('\n').split(',', 1)
    print(f'{country}\t{bird}')

