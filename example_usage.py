#!/usr/bin/python

'''Simple example usage of Mindwave headset

Connects to the headset, and continuously prints the data it reads
in a legible format. Raw data is not shown.
'''

from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work

h = FakeHeadset()
#h = BluetoothHeadset()
while True:
  point = h.readDatapoint()
  print point

# That's it. Easy enough.
