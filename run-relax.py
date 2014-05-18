#!/usr/bin/env python

import sys
import time
from Mindwave.mindwave import BluetoothHeadset, FakeHeadset
# Note: on OS X, BluetoothHeadset will not work
from parameters import SharedParameters
from threads import HeadsetThread
from gameplay import GameObject, ResponsiveRedVersusBlue
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist
from effects.base import RGBLayer, TechnicolorSnowstormLayer, WhiteOutLayer, ColorLayer

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
        shared_params.targetFrameRate = 100.0
        shared_params.use_keyboard_input = False
    # shared_params.debug = False

    player1 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_ONE_ADDRESS)
    player2 = FakeHeadset(random_data = True) if test else BluetoothHeadset(PLAYER_TWO_ADDRESS)

    effect_sequence_low = Playlist( [ 
        [ColorLayer([1., 0., 0.])] ] )

    effect_sequence_high = Playlist( [ 
        [ColorLayer([0., 0., 1.])] ] )

    renderer_low = Renderer({'relax_harder': effect_sequence_low})
    renderer_high = Renderer({'relax_harder': effect_sequence_high})
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
