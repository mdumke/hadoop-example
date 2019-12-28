#!/usr/bin/env python

"""
Generate n lines of random content of the form <name>,"<text>", where
n is passed as argument, or is 10 by default

usage: python generate_posts.py 3
"""

import sys
import random
from faker import Faker
from faker.providers import person

if __name__ == '__main__':
    try:
        n = int(sys.argv[1])
    except IndexError:
        n = 10

    fake = Faker()
    fake.add_provider(person)

    for _ in range(n):
        print('%s,"%s"' % (fake.first_name(), fake.text(random.randint(30, 50))))

