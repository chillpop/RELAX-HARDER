#!/usr/bin/env python

import time
import sys
import subprocess
from parameters import EEGInfo, SharedParameters
from Mindwave.mindwave import Datapoint

class RelaxReflector:
    """Utility to output headset and game data over Bluetooth LE
    """
    params = None
    # last_game_data_time = None

    process = None

    @classmethod
    def create_reflector(self, params):
        self.params = params
        self.process = subprocess.Popen(['node', 'serial-central.js'], 
            stdin=subprocess.PIPE)#, cwd='')

    @classmethod
    def shutdown_reflector(self):
        self.process.communicate('q\n')
        self.process.terminate()

    @classmethod
    def headset_data_changed(self, use_eeg2=False):
        eeg = None
        if use_eeg2 == True:
            eeg = self.params.eeg1
            self._send_data(player_one_data=eeg)
        else:
            eeg = self.params.eeg2
            self._send_data(player_two_data=eeg)

    @classmethod
    def game_data_changed(self, game_time=None):
        self._send_data(game_time=game_time)

    @classmethod
    def _send_data(self, player_one_data=None, player_two_data=None, game_time=None):
        def eeg_to_string(eeg):
            if eeg == None:
                return '[]'
            return '[{},{},{},{},{},{}]'.format(eeg.meditation, eeg.meditation_avg, eeg.attention, eeg.attention_avg, eeg.on, eeg.poor_signal)

        game_string = '[]'
        if game_time != None:
            game_string = '[{},{}]'.format(self.params.percentage, game_time)

        data_string = '{},{},{}\n'.format(eeg_to_string(player_one_data), eeg_to_string(player_two_data), game_string)

        self.process.communicate(data_string)
        # self.process.stdin.write(data_string)
        # self.process.stdin.flush()


if __name__ == '__main__':
    # A basic main function for testing
    params = SharedParameters()
    eeg = EEGInfo(Datapoint(), 0.234234, 0.345893794)
    eeg.attention = .5
    eeg.meditation = 0.2
    eeg.on = True
    eeg.poor_signal = False
    eeg.attention_avg = 0.234
    eeg.meditation_avg = 0.3485734598
    params.eeg1 = eeg
    params.eeg2 = eeg
    RelaxReflector.create_reflector(params)
    time.sleep(1.0)
    RelaxReflector.game_data_changed('test1')
    time.sleep(0.5)
    RelaxReflector.game_data_changed(5.234)
    RelaxReflector.headset_data_changed(use_eeg2=True)
    time.sleep(0.5)
    RelaxReflector.shutdown_reflector()

