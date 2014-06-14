#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

import sys
import copy
from controller import AnimationController
from renderer import Renderer
from playlist import Playlist
from effects.base import *
from parameters import SharedParameters
from gameplay import *
from game_effects import *
import colorsys

class SimpleController(AnimationController):

    def drawFrame(self):
        """Render a frame and send it to the OPC server"""
        self.advanceTime()
        self.checkInput()
        frame = numpy.zeros((self.params.num_pixels, 3))
        self.renderer_low.render(self.params, frame)
        
        # adjust brightness
        numpy.multiply(frame, self.params.brightness, frame)

        self.frameToHardwareFormat(frame)
        self.opc.putPixels(0, frame)
            
if __name__ == '__main__':
    def random_color():
        return colorsys.hsv_to_rgb(random.random(),1,1)

    yellowish = [1.0, 0.84, 0.28]
    greenish = [0.2, 0.4, 0.]

    purple = [0.2, 0., 0.3]
    pink = [0.7, 0.5, 0.4]

    playlist = Playlist([
                            # [OscillatingSpeedResponsiveTwoColorLayer(yellowish, greenish)],

                # [AnimatingWipeTransition(TwoColorSnowstormLayer(yellowish, greenish), 
                #     OscillatingSpeedResponsiveTwoColorLayer(yellowish, greenish),
                #     5.0, inverse=True)],

        [ OscillatingSpeedResponsiveTwoColorLayer(greenish, yellowish) ],
        [ OscillatingSpeedResponsiveTwoColorLayer(purple, pink, inverse=True) ],
        [ WhiteOutLayer() ],
        [ RGBLayer() ],
        [ SnowstormLayer() ],
        [ TechnicolorSnowstormLayer() ],
        [ ColorSnowstormLayer(random_color()) ],
        [ PulsingColorLayer(random_color()) ],
        [ PulsingColorLayer(random_color(), speed=2.0) ],
        [ OscillatingColorLayer(random_color(), speed=0) ],
        [ OscillatingColorLayer(random_color(), speed=5, length_of_peak=10) ],
        [ OscillatingColorLayer([0., 0., 1.], speed=1) ],
        [ OscillatingColorLayer([0., 0., 1.], speed=2) ],
        [ OscillatingColorLayer([0., 0., 1.], speed=3) ],
        [ OscillatingColorLayer(random_color(), speed=1) ],
        [ OscillatingColorLayer(random_color(), speed=-1) ],
        [ OscillatingColorLayer(random_color(), speed=-2.5, length_of_peak=30, minimum=0.5) ],
        [ ColorSnowstormLayer(random_color()), 
            OscillatingColorLayer(random_color(), minimum=0.2), 
            PulsingMultiplierLayer()],
        ])

    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
  
    ip_address = None
    if test and len(sys.argv) > 2:
        ip_address = sys.argv[2]

    shared_params = SharedParameters()
    shared_params.targetFrameRate = 100.0;

    renderer = Renderer(playlists={'all': playlist}, gamma=2.2)
    renderer_high = Renderer(playlists={'all': copy.copy(playlist)}, gamma=2.2)
    renderer.advanceCurrentPlaylist(fadeTime=0.001)
    controller = AnimationController(renderer_low=renderer, params=shared_params, server=ip_address, 
        game_object=None, renderer_high=renderer_high)
    controller.drawingLoop()

