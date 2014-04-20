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
        def __init__(self, point):
            self.attention = point.attention_scaled
            self.meditation = point.meditation_scaled
            self.on = point.headsetDataReady()
            self.poor_signal = point.poor_signal

        def __str__(self):
            return "Attn: {0}, Med: {1}, PoorSignal: {2}".format(
                self.attention, self.meditation, self.poor_signal) 

    def __init__(self, params, headset, use_eeg2=False):
        super(HeadsetThread,self).__init__(params)
        self.headset = headset
        self.use_eeg2 = use_eeg2;

    def run(self):
        while True: 
            point = self.headset.readDatapoint()
            eeg = HeadsetThread.EEGInfo(point)
            if self.use_eeg2 == True:
                self.params.eeg2 = eeg
            else:
                self.params.eeg1 = eeg
            if self.params.debug:
                print eeg

