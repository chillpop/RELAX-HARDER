#!/usr/bin/env python

import time
import numpy
import math
from parameters import SharedParameters, EEGInfo
from effects.base import EffectLayer, HeadsetResponsiveEffectLayer
from renderer import Renderer

MAX_DELTA = 1.0
MIN_DELTA = 0.05
CHANGE_IN_DELTA_PER_SECOND = 0.0025
ELAPSED_STARTUP_TIME = 2.0
TIME_AT_MAX = 3.0

DEFAULT_ATTRIBUTE = 'meditation'

class GameObject(object):
    """
    Class to calculate the game between two headset players
        """
    def __init__(self, params, renderer_low, renderer_high):
        self.params = params
        self.renderer_low = renderer_low
        self.renderer_high = renderer_high

        self.layer1 = None
        self.layer2 = None

        self.last_eeg1 = None
        self.last_eeg2 = None

        self.start_time = None
        self.win_time = None
        self.potential_winner = None
        self.winner = None

    def percentage_from_values(self, value1, value2):
        def delta_needed_to_win():
            #delta needed to win starts at a max value and slowly goes down over time
            elapsed_time = time.time() - (self.start_time + ELAPSED_STARTUP_TIME)
            elapsed_time = max(elapsed_time, 0)
            return max(MAX_DELTA - (CHANGE_IN_DELTA_PER_SECOND * elapsed_time), MIN_DELTA)

        percentage = 0.5
        #don't do anything unless we have both values
        if value1 > 0.001 and value2 > 0.001 and self.start_time != None:
            delta = value1 - value2
            #take the difference between the values
            #(delta / delta_needed_to_win) will be centered around zero
            percentage = delta / delta_needed_to_win()
            #make sure we don't go out of bounds [-1, 1]
            percentage = numpy.clip(percentage, -1.0, 1.0)
            #transform that into [0, 1]
            percentage = (1 + percentage) * 0.5
        return percentage

    def start(self, player_one_attr=DEFAULT_ATTRIBUTE, player_two_attr=DEFAULT_ATTRIBUTE):
        self.layer1 = HeadsetResponsiveEffectLayer(respond_to=player_one_attr, 
                                                    smooth_response_over_n_secs=self.params.frames_to_average)
        self.layer2 = HeadsetResponsiveEffectLayer(respond_to=player_two_attr, 
                                                    smooth_response_over_n_secs=self.params.frames_to_average)
        self.last_eeg1 = None
        self.last_eeg2 = None
        self.renderer_high.swapPlaylists(self.params.NO_HEADSET_STATE, fadeTime=0.1)
        self.renderer_low.swapPlaylists(self.params.NO_HEADSET_STATE, fadeTime=0.1)
        self.params.percentage = 0.5
        self.start_time = time.time()
        self.win_time = None
        self.potential_winner = None
        self.winner = None

    def change_effects(self, renderer, eeg, last_eeg):
        if eeg and eeg != last_eeg:
            if not eeg or not eeg.on:
                renderer.swapPlaylists(self.params.NO_HEADSET_STATE)
            else:
                renderer.swapPlaylists(self.params.PLAY_STATE)
            last_eeg = eeg
        return last_eeg

    def loop(self):
        self.last_eeg1 = self.change_effects(self.renderer_low, self.params.eeg1, self.last_eeg1)
        self.last_eeg2 = self.change_effects(self.renderer_high, self.params.eeg2, self.last_eeg2)

        value1 = self.layer1.calculate_response_level(params=self.params)
        value2 = self.layer2.calculate_response_level(params=self.params, use_eeg2=True)
        if value1 != None and value2 != None and self.winner == None:

            percentage = self.percentage_from_values(value1, value2)
            self.params.percentage = percentage

            if self.params.debug == True:
                NUM_PIXELS = 100
                p1_chars = int(round(percentage * NUM_PIXELS)) * '*'
                p2_chars = (NUM_PIXELS - len(p1_chars)) * '^'
                bar = p1_chars + p2_chars

                print 'value1: %f, value2: %f, percentage %f' % (value1, value2, percentage)
                print '|'+bar+'|'

            #winner must 'win' for a certain amount of time to be legit
            if percentage == 0.0 or percentage == 1.0:
                self.potential_winner = percentage
                if self.win_time == None:
                    self.win_time = time.time()
            else:
                self.potential_winner = None
            if self.potential_winner != None and (time.time() - self.win_time) > TIME_AT_MAX:
                self.winner = 'one' if self.potential_winner == 1.0 else 'two'
                print 'winner is player %s' % self.winner   
                # sys.exit(0)

class PercentageLayerMixer(EffectLayer):
    """An effect layer that computes a composite of two frames based on the current percentage 
        in the shared parameters."""
    def render(self, params, low_frame, high_frame, out_frame, mix_radius=3):
        length = len(out_frame)
        max_index = length - 1
        dividing_float = params.percentage * length
        dividing_index = int(round(dividing_float))
        mix_radius = max(mix_radius, 0)
        if params.percentage == 0.0:
            out_frame[:] = high_frame[:]
        elif dividing_index > max_index:
            out_frame[:] = low_frame[:]
        elif mix_radius == 0:
            # simple mixing over one pixel - smoother transitions between percentage levels
            idx = int(math.floor(dividing_float))
            #everything below the index is low_frame
            out_frame[:idx] = low_frame[:idx]
            # mix the pixel at the index based on the fractional value
            alpha = dividing_float - idx
            out_frame[idx] = (1 - alpha) * high_frame[idx] + alpha * low_frame[idx]
            idx += 1
            #everything above the index is high_frame
            out_frame[idx:] = high_frame[idx:]

        else:
            window_radius = mix_radius

            #shorten the window_radius if we're close to either end of the frame
            window_radius = min(window_radius, dividing_index)
            window_radius = min(window_radius, max_index - dividing_index)

            #calculate start and end indices, making sure they don't go out of bounds
            window_start = max(dividing_index - window_radius, 0)
            #include an extra 1 in window_end to include the dividing index itself
            window_end = min(dividing_index + window_radius, max_index) + 1
            window_length = 2 * window_radius + 1
            window_step = min(1.0 / window_length, 0.5)
            alpha = window_step
            #before window_start it is only values in the low_frame
            if window_start > 0:
                out_frame[:window_start] = low_frame[:window_start]
            for idx in range (window_start, window_end):
                out_frame[idx] += (1 - alpha) * low_frame[idx] + alpha * high_frame[idx]
                # print alpha
                alpha += window_step
            #after window_end it is only values in the high_frame
            if window_end < max_index:
                out_frame[window_end:] = high_frame[window_end:]
            # print ' %d +- %d = %d => (%d - %d)' % (dividing_index, window_radius, window_length, window_start, window_end)


class PercentageResponsiveEffectLayer(EffectLayer):
    """A layer effect that responds to the percentage of two MindWave headsets in some way.

    Two major differences from EffectLayer:
    1) Constructor expects one parameter:
       -- inverse: If this is true, the layer will respond to (1-response_level)
          instead of response_level
    2) Subclasses now only implement the render_responsive() function, which
       is the same as EffectLayer's render() function but has one extra
       parameter, response_level, which is the current EEG value of the indicated
       field (assumed to be on a 0-1 scale, or None if no value has been read yet).
    """
    def __init__(self, inverse=False):
        self.inverse = inverse;

    def render(self, params, frame):
        response_level = params.percentage
        if self.inverse:
            response_level = 1.0 - response_level
        self.render_responsive(params, frame, response_level)

    def render_responsive(self, params, frame, response_level):
        raise NotImplementedError(
            "Implement render_responsive() in your PercentageResponsiveEffectLayer subclass")

