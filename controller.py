#!/usr/bin/env python

from parameters import SharedParameters
from renderer import Renderer
from gameplay import GameObject, PercentageLayerMixer
import os
import socket
import time
import sys
import numpy
import math
import struct
import tty
import select
import termios

try:
    print "trying to use RPi.GPIO"
    import RPi.GPIO as GPIO
except ImportError, e:
    try:
        print "trying to use Adafruit_BBIO.GPIO"
        import Adafruit_BBIO.GPIO as GPIO
    except ImportError, e:
        print "both tries failed, not using GPIO"
      # This package does not exist on mac
        GPIO = None
        pass

def platform_is_raspberrypi():
    return GPIO != None and GPIO.__name__.startswith("RPi")

def get_key_or_none():
    c = None
    if select.select([sys.stdin], [], [], 0.0001) == ([sys.stdin], [], []):
        c = sys.stdin.read(1)
    return c

class AnimationController(object):
    """Manages the main animation loop. Each EffectLayer from the 'layers' list is run in order to
       produce a final frame of LED data which we send to the OPC server. This class manages frame
       rate control, and handles the advancement of time in EffectParameters.
       """

    def __init__(self, game_object, renderer_low, renderer_high, params=None, server=None):
        self.params = params or SharedParameters()
        self.pixel_writer = FastOPC(server=server)
        self.game_object = game_object
        self.layer_mixer = PercentageLayerMixer()
        self.renderer_low = renderer_low
        self.renderer_high = renderer_high

        self._fpsFrames = 0
        self._fpsTime = 0
        self._fpsLogPeriod = 0.5    # How often to log frame rate

        if GPIO != None:
            if platform_is_raspberrypi():
                GPIO.setmode(GPIO.BCM)
            def addGPIOButtonCallback(pin, callback, hold_time):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin, 
                    GPIO.FALLING, 
                    callback=callback, 
                    bouncetime=hold_time)

            oneSecondMs = 1000
            # restart game button
            addGPIOButtonCallback(self.params.reset_button_pin, restartGameFromButtonPress, oneSecondMs)
            # shutdown button
            addGPIOButtonCallback(self.params.shutdown_button_pin, shutdownFromButtonPress, oneSecondMs)

    def restartGameFromButtonPress(button_pin):
        print 'restart game button pressed'
        if self.game_object != None:
            self.game_object.start()

    def shutdownFromButtonPress(button_pin):
        print 'shutting down!!!'
        # NOTE: this must be run as root for shutdown to work
        os.system("sudo shutdown -h now")

    def advanceTime(self):
        """Update the timestep in EffectParameters.

           This is where we enforce our target frame rate, by sleeping until the minimum amount
           of time has elapsed since the previous frame. We try to synchronize our actual frame
           rate with the target frame rate in a slightly loose way which allows some jitter in
           our clock, but which keeps the frame rate centered around our ideal rate if we can keep up.

           This is also where we log the actual frame rate to the console periodically, so we can
           tell how well we're doing.
           """

        now = time.time()
        dt = now - self.params.time
        dtIdeal = 1.0 / self.params.targetFrameRate

        if dt > dtIdeal * 2:
            # Big jump forward. This may mean we're just starting out, or maybe our animation is
            # skipping badly. Jump immediately to the current time and don't look back.

            self.params.time = now
            self.params.delta_t = dt
        else:
            # We're approximately keeping up with our ideal frame rate. Advance our animation
            # clock by the ideal amount, and insert delays where necessary so we line up the
            # animation clock with the real-time clock.

            self.params.time += dtIdeal
            self.params.delta_t = dtIdeal
            if dt < dtIdeal:
                time.sleep(dtIdeal - dt)

        # Log frame rate

        self._fpsFrames += 1
        if self.params.debug and now > self._fpsTime + self._fpsLogPeriod:
            fps = self._fpsFrames / (now - self._fpsTime)
            self._fpsTime = now
            self._fpsFrames = 0
            sys.stderr.write("%7.2f FPS\n" % fps)

    def checkInput(self):
        if self.params.use_keyboard_input:
            # http://stackoverflow.com/a/1450063
            # poll for keyboard input
            i,o,e = select.select([sys.stdin], [], [], 0)
            if sys.stdin in i:
                c = sys.stdin.read(1)
                if c == 'w':
                    self.params.brightness = min(1.0, self.params.brightness + 0.1)
                elif c == 's':
                    self.params.brightness = max(0.0, self.params.brightness - 0.1)
                elif c == 'r' and self.game_object != None:
                    self.game_object.start()
                elif c == 'z' and self.renderer_low != None:
                    self.renderer_low.advanceCurrentPlaylist()
                elif c == 'x' and self.renderer_high != None:
                    self.renderer_high.advanceCurrentPlaylist()
                elif c == ']' and self.game_object == None:
                    self.params.percentage = min(self.params.percentage + 0.01, 1.0)
                elif c == '[' and self.game_object == None:
                    self.params.percentage = max(self.params.percentage - 0.01, 0.0)

    def renderLayers(self):
        """Generate a complete frame of LED data by rendering each layer."""

        # Note: You'd think it would be faster to use float32 on the rPI, but
        #       32-bit floats take a slower path in NumPy sadly.
        frame = numpy.zeros((self.params.num_pixels, 3))

        low_frame = numpy.zeros((self.params.num_pixels, 3))
        self.renderer_low.render(self.params, low_frame)
        
        high_frame = numpy.zeros((self.params.num_pixels, 3))
        self.renderer_high.render(self.params, high_frame)

        #mix the frames together
        self.layer_mixer.render(self.params, low_frame, high_frame, frame, mix_radius=0)

        # adjust brightness
        numpy.multiply(frame, self.params.brightness, frame)
        return frame

    def frameToHardwareFormat(self, frame):
        """Convert a frame in our abstract floating-point format to the specific format used
           by the OPC server. Does not clip to the range [0,255].

           Modifies 'frame' in-place.
           """
        numpy.multiply(frame, 255, frame)

    def drawFrame(self):
        """Render a frame and send it to the OPC server"""
        self.advanceTime()
        self.checkInput()
        if self.game_object != None:
            self.game_object.loop()
        pixels = self.renderLayers()
        self.frameToHardwareFormat(pixels)
        self.pixel_writer.putPixels(pixels)

    def drawingLoop(self):
        """Render frames forever or until keyboard interrupt"""
        #save existing terminal settings
        old_settings = None
        if self.params.use_keyboard_input:
            old_settings = termios.tcgetattr(sys.stdin)
        try:
            if self.params.use_keyboard_input:
                tty.setcbreak(sys.stdin.fileno())
            while True:
                self.drawFrame()
        except KeyboardInterrupt:
            pass
        finally:
            if self.params.use_keyboard_input:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

class PixelWriter(object):
    def putPixels(self, pixels):
        """Send a list of 8-bit colors to the LED hardware.
           'Pixels' is an array of any shape, in RGB order. Pixels range from 0 to 255.

           They need not already be clipped to this range; that's taken care of here.
           'pixels' is clipped in-place. If any values are out of range, the array is modified.
           """
        pass

class FastOPC(PixelWriter):
    """High-performance Open Pixel Control client, using Numeric Python.
       By default, assumes the OPC server is running on localhost. This may be overridden
       with the OPC_SERVER environment variable, or the 'server' keyword argument.
       """

    def __init__(self, channel=0, server=None):
        self.channel = channel
        self.server = server or os.getenv('OPC_SERVER') or '127.0.0.1:7890'
        self.host, port = self.server.split(':')
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def putPixels(self, pixels):
        """Send a list of 8-bit colors to the indicated channel. (OPC command 0x00).
           'Pixels' is an array of any shape, in RGB order. Pixels range from 0 to 255.

           They need not already be clipped to this range; that's taken care of here.
           'pixels' is clipped in-place. If any values are out of range, the array is modified.
           """

        numpy.clip(pixels, 0, 255, pixels)
        packedPixels = pixels.astype('B').tostring()
        header = struct.pack('>BBH',
            self.channel,
            0x00,  # Command
            len(packedPixels))
        self.socket.send(header + packedPixels)
