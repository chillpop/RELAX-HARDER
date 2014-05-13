#!/usr/bin/env python

import sys
import time
from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work
from parameters import SharedParameters
from threads import HeadsetThread
from gameplay import GameObject
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist
from effects.base import RGBLayer, TechnicolorSnowstormLayer, ResponsiveGreenHighRedLow

PLAYER_ONE_ADDRESS = '74:E5:43:BE:39:71'
PLAYER_ONE_COLOR = 255, 0, 0
PLAYER_TWO_ADDRESS = '74:E5:43:B1:96:E0'
PLAYER_TWO_COLOR = 0, 0, 255

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

    game = GameObject(shared_params)
    game.start()
    renderer = Renderer({'relax_harder': effect_sequence})
    controller = AnimationController(game_object=game, renderer=renderer, params=shared_params, server=ip_address)

    threads = [
        HeadsetThread(shared_params, player1),        
        HeadsetThread(shared_params, player2, use_eeg2=True),
    ]
    for thread in threads:
        thread.start()

    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
