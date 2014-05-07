#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

import sys
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist
from effects.base import *
from effects.drifters import *
from effects.impulses import *
from parameters import SharedParameters

            
if __name__ == '__main__':
    playlist = Playlist([[
        # TimedColorDrifterLayer([(0,1,0), (0,1,1), (1,0,1)], 5), 
        # ResponsiveColorDrifterLayer([(1,0,0), (0,0,1)]), 
        # SnowstormLayer(),
        TechnicolorSnowstormLayer(),
    ]])

    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
  
    ip_address = None
    if test and len(sys.argv) > 2:
        ip_address = sys.argv[2]

    shared_params = SharedParameters()
    shared_params.targetFrameRate = 100.0;

    renderer = Renderer(playlists={'all': playlist}, gamma=2.2)
    controller = AnimationController(renderer=renderer, params=shared_params, server=ip_address)
    controller.drawingLoop()
