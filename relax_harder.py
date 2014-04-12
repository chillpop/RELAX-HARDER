#!/usr/bin/python

'''Simple example usage of Mindwave headset

Connects to the headset, and continuously prints the data it reads
in a legible format. Raw data is not shown.
'''

from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work
from OpenPixelControl import opc
import math

NUM_PIXELS = 120
MAX_VALUE = 100

def bar_from_datapoint(point, reverse=False):
  #scale to be half the number of pixels max
  scale = (NUM_PIXELS / 2.0) / MAX_VALUE
  meditation = int(math.floor(point.meditation * scale))
  meditation_max = int(math.ceil(MAX_VALUE * scale))
  stars = meditation * '*'
  blanks = (meditation_max - meditation) * '-'
  bar = stars + blanks
  if reverse:
    bar = bar[::-1]
  return bar

def pixels_from_bar(bar):
  pixels = []
  for c in bar:
    # gray unless we see a star
    rgb = [128, 128, 128]
    if c == '*':
      rgb = [255, 0, 0]
    rgb = tuple(rgb)
    pixels.append(rgb)
  return pixels

#-------------------------------------------------------------------------------
# connect to OPC server

IP_PORT = '127.0.0.1:7890'
opcClient = opc.Client(IP_PORT)
if opcClient.can_connect():
    print '    connected to OPC server on port %s' % IP_PORT
else:
    # can't connect, but keep running in case the server appears later
    print '    WARNING: could not connect to OPC server on port %s' % IP_PORT
print

player1 = FakeHeadset()
player2 = FakeHeadset()
while True:
  point1 = player1.readDatapoint()
  point2 = player2.readDatapoint()

  fullbar = bar_from_datapoint(point1) + bar_from_datapoint(point2, True)
  print '|' + fullbar + '|'
  opcClient.put_pixels(pixels_from_bar(fullbar))

