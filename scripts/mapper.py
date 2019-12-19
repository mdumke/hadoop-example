#!/usr/bin/env python

"""
Read from STDIN and output key-value pair as '<user><TAB>1'
"""

import sys

for line in sys.stdin.readlines():
    user, text = line.split(',')
    print('%s\t1' % user)

