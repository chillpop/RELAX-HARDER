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

def generate_player_renderer(params, color, similar_color, inverse=False):
    # hsv = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    # similar_color = colorsys.hsv_to_rgb(hsv[0] + 0.15, hsv[1], hsv[2])
    regular_play = Playlist([
        [OscillatingSpeedResponsiveTwoColorLayer(color, similar_color, inverse=inverse)]
        ])

    no_headset = Playlist([
        [SnowstormLayer()]
        ])

    winner = Playlist([
        [TwoColorSnowstormLayer(color, similar_color)]
        ])

    #make a countdown mixer layer that performs an animating wipe from one effect to another
    #wipe between regular gameplay effect and winning effect?
    countdown = Playlist([
        [AnimatingWipeTransition(TwoColorSnowstormLayer(color, similar_color), 
            OscillatingSpeedResponsiveTwoColorLayer(color, similar_color, inverse=inverse),
            params.COUNTDOWN_TIME, inverse=(not inverse))]
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
        self.color_one = numpy.array(color_one)
        self.color_two = numpy.array(color_two)
        self.color_frame = None
        self.length_of_peak = length_of_peak
        self.speed = speed

    def create_two_color_frame(self, frame, phase_shift=0.0):
        temp_frame = numpy.zeros((self.length_of_peak, 3))
        step = 1.0 / self.length_of_peak
        for x in range(0, self.length_of_peak):
            scale = oscillating_value(x, step, 0.0, 1.0, phase_shift)
            color_value = self.color_one * scale + self.color_two * (1.0 - scale)
            temp_frame[x] = color_value
        return temp_frame

    def render(self, params, frame):
        self.color_frame = self.create_two_color_frame(frame, params.time * self.speed)
        numpy.add(frame, numpy.resize(self.color_frame, frame.shape), frame)


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
        numpy.add(frame, numpy.resize(self.color_frame, frame.shape), frame)

class AnimatingWipeTransition(EffectLayer):
    def __init__(self, start_effect, end_effect, duration, inverse=False, start_alpha=0.0, end_alpha=0.5):
        self.start_effect = start_effect
        self.end_effect = end_effect
        self.duration = duration
        self.inverse = inverse
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        self.alpha_span = end_alpha - start_alpha
        if inverse:
            # 0 - .5 => 1 - .5 span .5 => -.5
            # .2 - .7 => .8 - .3 span .5 => -.5
            self.start_alpha = 1.0 - start_alpha
            self.alpha_span = -self.alpha_span
            self.start_effect = end_effect
            self.end_effect = start_effect
            #inverse should transition from 
        self.start_time = None
        self.end_time = None
        self.last_time = None
        self.current_alpha = self.start_alpha

    def render(self, params, frame):
        #should we start or start over?
        if self.start_time == None or self.last_time + params.delta_t < params.time:
            self.start_time = params.time
            self.end_time = params.time + self.duration
            self.current_alpha = self.start_alpha
        elapsed_time = (params.time - self.start_time) / self.duration
        alpha = self.start_alpha + elapsed_time * self.alpha_span
        if elapsed_time > 1.0:
            alpha = self.start_alpha + self.alpha_span

        #remember the last time here so we can tell when we should start over
        self.last_time = params.time

        if alpha == 0.0:
            self.start_effect.safely_render(params, frame)
        elif alpha == 1.0:
            self.end_effect.safely_render(params, frame)
        else:
            #render alpha amount of start effect and (1 - alpha) of end effect
            dividing_float = alpha * len(frame)

            # simple mixing over one pixel
            idx = int(math.floor(dividing_float))
            # print idx
            #make a low frame for start_effect to render into
            # end_idx = min(idx + 1, len(frame) - 1)
            low_frame = frame[:idx+1]
            high_frame = frame[idx:]

            self.end_effect.safely_render(params, low_frame)
            # low_pixel = frame[idx]
            # frame[idx] = [0., 0., 0.]
            self.start_effect.safely_render(params, high_frame)
            # high_pixel = frame[idx]

            # # mix the pixel at the index based on the fractional value
            # mix_alpha = dividing_float - idx
            # frame[idx] = (1 - mix_alpha) * high_pixel + alpha * low_pixel
