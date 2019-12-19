#!/usr/bin/env python

"""
Read user-count pairs from STDIN and output aggregated counts
"""

import sys

current_user = None

for line in sys.stdin.readlines():
    user, count = line.split('\t')

    if user != current_user:
        if current_user is not None:
            print('%s\t%s' % (user, total))
        current_user = user
        total = int(count)
    else:
        total += int(count)

print('%s\t%s' % (user, total))
