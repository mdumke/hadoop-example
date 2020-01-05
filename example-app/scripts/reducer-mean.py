#!/usr/bin/env python

import sys

counts = [int(line.split('\t')[1]) for line in sys.stdin.readlines()]
print(sum(counts) / len(counts))

