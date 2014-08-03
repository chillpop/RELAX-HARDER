#!/usr/bin/env python

import threading
import random
import time
import sys
from parameters import EEGInfo

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

    def __init__(self, params, headset, use_eeg2=False):
        super(HeadsetThread,self).__init__(params)
        self.headset = headset
        self.use_eeg2 = use_eeg2;
        self.attention_list = []
        self.meditation_list = []

    def run(self):
        while True:
            point = self.headset.readDatapoint()
            if not point:
                #try to reconnect if we lose the connection
                self.headset.disconnect
                self.headset.socket = None
                continue

            self.attention_list.append(point.attention_scaled)
            self.meditation_list.append(point.meditation_scaled)
            if len(self.meditation_list) > self.params.frames_to_average:
                self.meditation_list.pop(0)
                self.attention_list.pop(0)
            def avg(l): return (sum(l) / len(l))
            # print 'meditation list: %r -> %.2f' % (self.meditation_list, avg(self.meditation_list))

            eeg = EEGInfo(point, avg(self.attention_list), avg(self.meditation_list))

            if self.use_eeg2 == True:
                self.params.eeg2 = eeg
            else:
                self.params.eeg1 = eeg
            if self.params.debug:
                print eeg

