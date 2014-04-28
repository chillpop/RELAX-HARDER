#!/usr/bin/env python

import threading
import random
import time
import sys

class ParamThread(threading.Thread):
    """
    Base class for daemon threads that operate on a SharedParameters object
    """
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.daemon = True
        self.params = params


class HeadsetThread(ParamThread):
    """
    Polls the Mindwave headset. Each time a new point is received, creates an 
    EEGInfo object and stores it in params.
    """ 
    
    class EEGInfo:
        """
        Extracts/stores all the headset info that the effects might actually care about.
        Attention and meditation values are scaled to floats in the range [0,1].
        """
        def __init__(self, point, attention_avg, meditation_avg):
            self.attention = point.attention_scaled
            self.meditation = point.meditation_scaled
            self.on = point.headsetDataReady()
            self.poor_signal = point.poor_signal
            self.attention_avg = attention_avg
            self.meditation_avg = meditation_avg

        def __str__(self):
            return "Attn: {0}, Med: {1}, PoorSignal: {2}".format(
                self.attention, self.meditation, self.poor_signal) 

    def __init__(self, params, headset, use_eeg2=False):
        super(HeadsetThread,self).__init__(params)
        self.headset = headset
        self.use_eeg2 = use_eeg2;
        self.attention_list = []
        self.meditation_list = []

    def run(self):
        while True:
            point = self.headset.readDatapoint()

            self.attention_list.append(point.attention_scaled)
            self.meditation_list.append(point.meditation_scaled)
            if len(self.meditation_list) > self.params.frames_to_average:
                self.meditation_list.pop(0)
                self.attention_list.pop(0)
            def avg(l): return (sum(l) / len(l))
            # print 'meditation list: %r -> %.2f' % (self.meditation_list, avg(self.meditation_list))

            eeg = HeadsetThread.EEGInfo(point, avg(self.attention_list), avg(self.meditation_list))

            if self.use_eeg2 == True:
                self.params.eeg2 = eeg
            else:
                self.params.eeg1 = eeg
            if self.params.debug:
                print eeg

