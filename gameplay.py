#!/usr/bin/env python

import time
import numpy
from parameters import SharedParameters, EEGInfo
from effects.base import HeadsetResponsiveEffectLayer

MAX_DELTA = 1.0
MIN_DELTA = 0.05
CHANGE_IN_DELTA_PER_SECOND = 0.01
ELAPSED_STARTUP_TIME = 2.0
TIME_AT_MAX = 3.0

DEFAULT_ATTRIBUTE = 'meditation'

class GameObject(object):
    """
    Class to calculate the game between two headset players
        """
    def __init__(self, params):
        self.params = params

        self.layer1 = None
        self.layer2 = None

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

        self.start_time = time.time()
        self.win_time = None
        self.potential_winner = None
        self.winner = None

    def loop(self):
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
