
class SharedParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """
    num_pixels = 120
    time = 0
    targetFrameRate = 59.0     # XXX: Want to go higher, but gl_server can't keep up!
    eeg1 = None
    eeg2 = None
    debug = True
