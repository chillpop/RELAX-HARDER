#!/usr/bin/env python

x_spacing = 0.11  # m
y_value = 0
z_value = -1
num_points = 120
lines = []
for c in range(-(num_points/2), (num_points/2)) :
    lines.append('  {"point": [%.2f, %.2f, %.2f]}' %
                 (c*x_spacing, y_value, z_value))
print '[\n' + ',\n'.join(lines) + '\n]'
