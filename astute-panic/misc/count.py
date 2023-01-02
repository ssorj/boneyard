#!/usr/bin/python

from plano import *
from collections import defaultdict

codes = read("codes.txt")

counts = defaultdict(int)

for char in codes:
    counts[char] += 1

pprint(counts)
