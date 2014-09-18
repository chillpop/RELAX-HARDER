#!/usr/bin/env python

import sys
import time
from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work
from parameters import SharedParameters
from threads import HeadsetThread
from gameplay import GameObject
from game_effects import generate_player_renderer
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist

PLAYER_ONE_ADDRESS = '74:E5:43:BE:39:71'
PLAYER_TWO_ADDRESS = '74:E5:43:B1:96:E0'

if __name__ == '__main__':

    num_args = len(sys.argv)
    test = num_args > 1 and sys.argv[1] == 'test'
  
    ip_address = None
    if test and num_args > 2:
        ip_address = sys.argv[2]
    elif num_args > 1:
        ip_address = sys.argv[1]

    # ip_address = '192.168.7.2:7890'
    
    shared_params = SharedParameters()
    if not test:
        shared_params.targetFrameRate = 100.0
        shared_params.use_keyboard_input = False
        shared_params.debug = False

    player1 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_ONE_ADDRESS)
    player2 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_TWO_ADDRESS)

    yellowish = [1.0, 0.84, 0.28]
    greenish = [0.2, 0.4, 0.]

    purple = [0.2, 0., 0.3]
    pink = [0.7, 0.5, 0.4]

    renderer_low = generate_player_renderer(shared_params, purple, pink, inverse=True)
    renderer_high = generate_player_renderer(shared_params, greenish, yellowish)
    game = GameObject(shared_params, renderer_low, renderer_high)
    game.start()
    controller = AnimationController(game_object=game, 
        renderer_low=renderer_low, renderer_high=renderer_high, params=shared_params, server=ip_address)

    threads = [
        HeadsetThread(shared_params, player1),        
        HeadsetThread(shared_params, player2, use_eeg2=True),
    ]
    for thread in threads:
        thread.start()

    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
