#!/usr/bin/env python

import numpy
import math
import time
import colorsys
import random
from parameters import SharedParameters
from renderer import Renderer
from playlist import Playlist
from effects.base import EffectLayer, RGBLayer, SnowstormLayer, TechnicolorSnowstormLayer, WhiteOutLayer, ColorLayer
from gameplay import PercentageResponsiveEffectLayer

def generate_player_renderer(params, color):
    regular_play = Playlist([
        [PulsingColorLayer(color, 1.0, 0.5, 1.0, random.random())]
        ])

    no_headset = Playlist([
        [ColorSnowstormLayer(color)]
        ])

    all_lists = {params.PLAY_STATE: regular_play,
                params.NO_HEADSET_STATE: no_headset}
    return Renderer(all_lists, activePlaylist=params.NO_HEADSET_STATE)

def oscillating_value(input_value, rate_of_change, minimum, span, phase_shift):	
	cycle = 2.0 * math.pi
	radians = rate_of_change * cycle * input_value + (phase_shift * cycle)
	scale = minimum + span * 0.5 * (math.cos(radians) + 1)
	return scale

class ColorSnowstormLayer(ColorLayer):
	"""A color noise layer"""
    def render(self, params, frame):
    	temp_frame = numpy.zeros_like(frame)
    	temp_frame[:] = self.color
    	numpy.multiply(temp_frame, numpy.random.rand(params.num_pixels, 1), temp_frame)
        numpy.add(frame, temp_frame, frame)

class PulsingColorLayer(ColorLayer):
	"""A layer that pulses a color value"""
	def __init__(self, color, speed=1.0, minimum=0.5, maximum=1.0, phase=0.0):
		super(PulsingColorLayer,self).__init__(color)
		self.speed = speed
		self.minimum = max(minimum, 0.0)
		self.maximum = min(maximum, 1.0)
		self.span = self.maximum - self.minimum
		self.phase_shift = phase * math.pi * 2

	def render(self, params, frame):
		scale = oscillating_value(params.time, self.speed, self.minimum, self.span, self.phase_shift)
		color_value = numpy.multiply(self.color, scale)

		numpy.add(frame, color_value, frame)

class PulsingMultiplierLayer(EffectLayer):
	"""A layer that pulses the brightness of all layers below it"""
	def __init__(self, speed=1.0, minimum=0.5, maximum=1.0, phase=0.0):
		self.speed = speed
		self.minimum = max(minimum, 0.0)
		self.maximum = min(maximum, 1.0)
		self.span = self.maximum - self.minimum
		self.phase_shift = phase * math.pi * 2

	def render(self, params, frame):
		scale = oscillating_value(params.time, self.speed, self.minimum, self.span, self.phase_shift)
		numpy.multiply(frame, scale, frame)
