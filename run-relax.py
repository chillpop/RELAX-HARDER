#!/usr/bin/python

'''Simple example usage of Mindwave headset

Connects to the headset, and continuously prints the data it reads
in a legible format. Raw data is not shown.
'''

import sys
import time
from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work
from parameters import SharedParameters
from threads import HeadsetThread
from effects.base import EffectParameters
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist
from effects.base import RGBLayer, TechnicolorSnowstormLayer, ResponsiveGreenHighRedLow

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

if __name__ == '__main__':

    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
  
    ip_address = None
    if test and len(sys.argv) > 2:
        ip_address = sys.argv[2]

    # ip_address = '192.168.7.2:7890'
    
    shared_params = SharedParameters()
    if not test:
        shared_params.targetFrameRate = 100.0;
    shared_params.debug = False

    player1 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_ONE_ADDRESS)
    player2 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_TWO_ADDRESS)

    effect_sequence = Playlist( [ 
        [ResponsiveGreenHighRedLow(respond_to='meditation')] ] )

    renderer = Renderer({'relax_harder': effect_sequence})
    controller = AnimationController(renderer=renderer, params=shared_params, server=ip_address)

    threads = [
        HeadsetThread(shared_params, player1),        
        HeadsetThread(shared_params, player2, use_eeg2=True),
    ]
    for thread in threads:
        thread.start()

    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
