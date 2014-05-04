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
import numpy

NUM_PIXELS = 120

PLAYER_ONE_ADDRESS = '74:E5:43:BE:39:71'
PLAYER_ONE_CHAR = '*'
PLAYER_ONE_COLOR = 255, 0, 0
PLAYER_TWO_ADDRESS = '74:E5:43:B1:96:E0'
PLAYER_TWO_CHAR = '^'
PLAYER_TWO_COLOR = 0, 0, 255

MAX_DELTA = 1.0
MIN_DELTA = 0.05
CHANGE_IN_DELTA_PER_SECOND = 0.01
ELAPSED_STARTUP_TIME = 2.0
TIME_AT_MAX = 2.0

start_time = time.time()

def delta_needed_to_win():
    """delta needed to win starts at a max value and slowly goes down over time
    """
    elapsed_time = time.time() - (start_time + ELAPSED_STARTUP_TIME)
    elapsed_time = max(elapsed_time, 0)
    return max(MAX_DELTA - (CHANGE_IN_DELTA_PER_SECOND * elapsed_time), MIN_DELTA)

def percentage_from_values(value1, value2):
    percentage = 0.5
    #don't do anything unless we have both values
    if value1 > 0.001 and value2 > 0.001:
        delta = value1 - value2
        #take the difference between the values
        #(delta / delta_needed_to_win) will be centered around zero
        percentage = delta / delta_needed_to_win()
        #make sure we don't go out of bounds [-1, 1]
        percentage = numpy.clip(percentage, -1.0, 1.0)
        #transform that into [0, 1]
        percentage = (1 + percentage) * 0.5
    return percentage

def bar_from_percentage(percentage):
    p1_chars = int(round(percentage * NUM_PIXELS)) * PLAYER_ONE_CHAR
    p2_chars = (NUM_PIXELS - len(p1_chars)) * PLAYER_TWO_CHAR
    bar = p1_chars + p2_chars
    return bar

def pixels_from_bar(bar):
    pixels = []
    for c in bar:
        # off unless we see a character we know
        rgb = 0, 0, 0
        if c == PLAYER_ONE_CHAR:
            rgb = PLAYER_ONE_COLOR
        elif c == PLAYER_TWO_CHAR:
            rgb = PLAYER_TWO_COLOR
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

    player1 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_ONE_ADDRESS)
    player2 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_TWO_ADDRESS)

    threads = [
        HeadsetThread(shared_params, player1),        
        HeadsetThread(shared_params, player2, use_eeg2=True),
    ]
    for thread in threads:
        thread.start()

    # start the lights
    time.sleep(0.05)

    fps = 60.0

    win_time = None
    potential_winner = None

    point1 = None
    point2 = None
    p1 = None
    p2 = None

    while True:
        point1 = shared_params.eeg1
        point2 = shared_params.eeg2
      
        if point1 != None and point2 != None:
            def delta(p, point, steps = fps):
                if p == None:
                    p = point
                elif p.meditation_avg != point.meditation_avg:
                    p.meditation_avg += float(point.meditation_avg - p.meditation_avg) / steps
                return p

            p1 = delta(p1, point1)
            p2 = delta(p2, point2)
            percentage = percentage_from_values(p1.meditation_avg, p2.meditation_avg)
            fullbar = bar_from_percentage(percentage)
            print '%s' % fullbar
            print '%.4f %.4f %.4f -> %.4f' % (p1.meditation_avg, p2.meditation_avg, 
                delta_needed_to_win(), percentage)
            opcClient.put_pixels(pixels_from_bar(fullbar))

            #winner must 'win' for a certain amount of time to be legit
            if percentage == 0.0 or percentage == 1.0:
                potential_winner = percentage
                if win_time == None:
                    win_time = time.time()
            else:
                potential_winner = None
            if potential_winner != None and (time.time() - win_time) > TIME_AT_MAX:
                winning_player = 'one' if potential_winner == 0.0 else 'two'
                print 'winner is player %s' % winning_player
                sys.exit(0)

        time.sleep(1.0 / fps)
  
