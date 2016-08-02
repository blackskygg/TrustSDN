#!/usr/bin/python

import pstats

p = pstats.Stats("profile.log")
p.print_stats()
