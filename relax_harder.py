#!/usr/bin/python

'''Simple example usage of Mindwave headset

Connects to the headset, and continuously prints the data it reads
in a legible format. Raw data is not shown.
'''

import sys
import time
from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
from parameters import SharedParameters
from threads import HeadsetThread
# Note: on OS X, BluetoothHeadset will not work
from OpenPixelControl import opc
import math

NUM_PIXELS = 120

PLAYER_ONE_CHAR = '*'
PLAYER_TWO_CHAR = '^'

def bar_from_datapoints(point1, point2):
    m1 = point1.meditation
    m2 = point2.meditation
    span = max(m1, m2) - min(m1, m2)
    if span == 0 or (m1 < 0.1 and m2 < 0.1):
        return NUM_PIXELS * ' '
    percentage = m1 / (m1 + m2)

    p1_chars = int(math.ceil(percentage * NUM_PIXELS)) * PLAYER_ONE_CHAR
    p2_chars = (NUM_PIXELS - len(p1_chars)) * PLAYER_TWO_CHAR
    bar = p1_chars + p2_chars
    return bar

def pixels_from_bar(bar):
    pixels = []
    for c in bar:
        # off unless we see a character we know
        rgb = [0, 0, 0]
        if c == PLAYER_ONE_CHAR:
            rgb = [255, 0, 0]
        elif c == PLAYER_TWO_CHAR:
            rgb = [0, 0, 255]
        rgb = tuple(rgb)
        pixels.append(rgb)
    return pixels

def create_opc_client(ip_address = '127.0.0.1'):
    ip_address += ':7890'
    opcClient = opc.Client(ip_address)
    status_suffix = ' to OPC server at %s' % ip_address
    print 'connecting' + status_suffix
    if opcClient.can_connect():
        print '    connected' + status_suffix
    else:
        # can't connect, but keep running in case the server appears later
        print '    WARNING: could not connect' + status_suffix
    print
    return opcClient

if __name__ == '__main__':

    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
  
    #-------------------------------------------------------------------------------
    # connect to OPC server
    
    ip_address = None
    if test and len(sys.argv) > 2:
        ip_address = sys.argv[2]

    # ip_address = '192.168.7.2:7890'
    opcClient = create_opc_client(ip_address) if ip_address != None else create_opc_client()
    
    shared_params = SharedParameters()
    if not test:
        shared_params.targetFrameRate = 100.0; # let's go for it
    shared_params.debug = False

    player1 = FakeHeadset(random_data=True) if test else BluetoothHeadset()
    player2 = FakeHeadset(random_data=True) if test else BluetoothHeadset()

    threads = [
        HeadsetThread(shared_params, player1),        
        HeadsetThread(shared_params, player2, use_eeg2=True),
    ]
    for thread in threads:
        thread.start()

    # start the lights
    time.sleep(0.05)

    fps = 60.0
    frames_to_average = 5

    point1 = None
    point2 = None
    p1 = None
    p2 = None

    while True:
        point1 = shared_params.eeg1
        point2 = shared_params.eeg2
      
        if point1 != None and point2 != None:
            def delta(p, point, steps=fps):
                if p == None:
                    p = point
                elif p.meditation != point.meditation:
                    p.meditation += float(point.meditation - p.meditation) / steps
                return p

            p1 = delta(p1, point1)
            p2 = delta(p2, point2)
            fullbar = bar_from_datapoints(p1, p2)
            print '|%s| %d\t%d' % (fullbar, int(p1.meditation*100), int(p2.meditation*100))
            opcClient.put_pixels(pixels_from_bar(fullbar))
        time.sleep(1.0/fps)
  
