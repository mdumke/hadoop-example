"""
Generator for bird observation data.

usage: python birds.py -n 10

Each observation has the format <species name>,<country code>
"""

import sys
import random

birds = ['Crow', 'Peacock', 'Dove', 'Sparrow', 'Goose', 'Ostrich', 'Pigeon',
         'Turkey', 'Hawk', 'Bald eagle', 'Raven', 'Parrot', 'Flamingo',
         'Seagull', 'Swallow', 'Blackbird', 'Penguin', 'Robin', 'Swan',
         'Owl', 'Stork', 'Woodpecker']

codes = ['BD', 'BF', 'CA', 'EE', 'GH', 'HT', 'IL', 'LY', 'MM', 'PK']


if __name__ == '__main__':
    try:
        n = int(sys.argv[2])
    except:
        print('usage example: python birds.py -n 20')
        sys.exit(1)

    for _ in range(n):
        print(f'{random.choice(birds)},{random.choice(codes)}')
