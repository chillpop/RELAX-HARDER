

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

class SharedParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """
    num_pixels = 120
    time = 0
    delta_t = 0
    targetFrameRate = 59.0     # XXX: Want to go higher, but gl_server can't keep up!
    eeg1 = None
    eeg2 = None
    percentage = 0.5
    brightness = 1.0

    COUNTDOWN_TIME = 5.0

    debug = False#True
    use_keyboard_input = True
    frames_to_average = 5

    button_pin = "P8_12"

    #game states
    PLAY_STATE = 'regular_play'
    NO_HEADSET_STATE = 'no_headset'
    WIN_STATE = 'winner'
    STARTUP_STATE = 'startup'
