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

def generate_player_renderer(params, color, inverse=False):
    hsv = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    similar_color = colorsys.hsv_to_rgb(hsv[0] + 0.15, hsv[1], hsv[2])
    regular_play = Playlist([
        [OscillatingSpeedResponsiveTwoColorLayer(color, similar_color, inverse=inverse)]
        ])

    no_headset = Playlist([
        [SnowstormLayer()]
        ])

    winner = Playlist([
        [TwoColorSnowstormLayer(color, similar_color)]
        ])

    countdown = Playlist([
        [WhiteOutLayer()]
        ])

    all_lists = {params.PLAY_STATE: regular_play,
                params.NO_HEADSET_STATE: no_headset,
                params.WIN_STATE: winner,
                params.STARTUP_STATE: countdown}
    return Renderer(all_lists, activePlaylist=params.NO_HEADSET_STATE)

def oscillating_value(input_value, rate_of_change, minimum, span, phase_shift=0.0):	
	cycle = 2.0 * math.pi
	radians = rate_of_change * cycle * input_value + (phase_shift * cycle)
	scale = minimum + span * 0.5 * (math.cos(radians) + 1)
	return scale

class ColorSnowstormLayer(ColorLayer):
	# """A color noise layer"""
    def render(self, params, frame):
    	temp_frame = numpy.zeros_like(frame)
    	temp_frame[:] = self.color
    	numpy.multiply(temp_frame, numpy.random.rand(len(frame), 1), temp_frame)
        numpy.add(frame, temp_frame, frame)

class TwoColorSnowstormLayer(ColorLayer):
    # """A color noise layer"""
    def __init__(self, color, other_color):
        super(TwoColorSnowstormLayer,self).__init__(color)
        self.other_color = other_color

    def render(self, params, frame):
        temp_frame = numpy.zeros_like(frame)
        temp_frame[:] = self.color
        numpy.multiply(temp_frame, numpy.random.rand(len(frame), 1), temp_frame)
        numpy.add(frame, temp_frame, frame)

        temp_frame[:] = self.other_color
        numpy.multiply(temp_frame, numpy.random.rand(len(frame), 1), temp_frame)
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

class OscillatingColorLayer(ColorLayer):
	def __init__(self, color, length_of_peak=20, speed=1.0, minimum=0.8, maximum=1.0):
		super(OscillatingColorLayer,self).__init__(color)
		self.color_frame = None
		self.length_of_peak = length_of_peak
		self.speed = speed
		self.minimum = max(minimum, 0.0)
		self.maximum = min(maximum, 1.0)
		self.span = self.maximum - self.minimum

	def create_color_frame(self, frame, phase_shift=0.0):
		temp_frame = numpy.zeros_like(frame)
		step = 1.0 / self.length_of_peak
		for x in range(0, len(frame)):
			scale = oscillating_value(x, step, self.minimum, self.span, phase_shift)
			color_value = numpy.multiply(self.color, scale)
			numpy.add(temp_frame[x], color_value, temp_frame[x])
		return temp_frame

	def render(self, params, frame):
		self.color_frame = self.create_color_frame(frame, params.time * self.speed)
		numpy.add(frame, self.color_frame, frame)

class OscillatingTwoColorLayer(EffectLayer):
    def __init__(self, color_one, color_two, length_of_peak=20, speed=1.0):
        self.color_one = color_one
        self.color_two = color_two
        self.color_frame = None
        self.length_of_peak = length_of_peak
        self.speed = speed

    def create_two_color_frame(self, frame, phase_shift=0.0):
        temp_frame = numpy.zeros_like(frame)
        step = 1.0 / self.length_of_peak
        for x in range(0, len(frame)):
            scale = oscillating_value(x, step, 0.0, 1.0, phase_shift)
            color_value_one = numpy.multiply(self.color_one, scale)
            color_value_two = numpy.multiply(self.color_two, 1.0 - scale)
            color_value = numpy.add(color_value_one, color_value_two)
            numpy.add(temp_frame[x], color_value, temp_frame[x])
        return temp_frame

    def render(self, params, frame):
        self.color_frame = self.create_two_color_frame(frame, params.time * self.speed)
        numpy.add(frame, self.color_frame, frame)


class OscillatingSpeedResponsiveTwoColorLayer(OscillatingTwoColorLayer):
    def __init__(self, color_one, color_two, length_of_peak=20, speed_low=3.5, speed_high=0.25, inverse=False):
        super(OscillatingSpeedResponsiveTwoColorLayer,self).__init__(
            color_one, color_two, length_of_peak)
        self.speed_low = speed_high
        self.span = speed_low - speed_high
        if inverse:
            self.speed_low = -speed_low
        self.speed = self.speed_low + 0.5 * self.span
        self.last_phase = 0.0

    def render(self, params, frame):
        alpha = params.percentage
        self.speed = self.speed_low + alpha * self.span
        phase = self.last_phase + params.delta_t * self.speed
        
        self.last_phase = phase
        self.color_frame = self.create_two_color_frame(frame, phase)
        numpy.add(frame, self.color_frame, frame)

