#!/usr/bin/env python

spacing = 0.11  # m
num_points = 120
lines = []
for c in range(-(num_points/2), (num_points/2)) :
    lines.append('  {"point": [%.2f, %.2f, %.2f]}' %
                 (c*spacing, 0, spacing))
print '[\n' + ',\n'.join(lines) + '\n]'
