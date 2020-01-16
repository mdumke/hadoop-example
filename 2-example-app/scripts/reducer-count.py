#!/usr/bin/env python

import sys

previous_country = None
birds = set()

for line in sys.stdin.readlines():
    country, bird = line.strip().split('\t')

    if country != previous_country:
        if previous_country is not None:
            print(f'{country}\t{len(birds)}')

        previous_country = country
        birds = set([bird])
    else:
        birds.add(bird)

print(f'{country}\t{len(birds)}')

