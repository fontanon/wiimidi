import os, sys

BUILD_PATHS = [os.path.join(os.getcwd(), 'build/lib.linux-x86_64-2.4/'),
               os.path.join(os.getcwd(), 'build/lib.darwin-8.5.0-Power_Macintosh-2.3/'),
               os.path.join(os.getcwd(), 'build/lib.darwin-8.8.1-i386-2.3/'),
               ]
sys.path = BUILD_PATHS + sys.path

import unittest
import rtmidi


class RtMidiInTest(unittest.TestCase):
    def setUp(self):
        self.rtmidi = rtmidi.RtMidiIn()

    def test_01_inputs_exist(self):
        self.assertEqual(self.rtmidi.getPortCount() > 0, True)

    def test_funcs(self):
        """ test that certain functions can be called. """
        self.rtmidi.openVirtualPort('myport')
        self.rtmidi.ignoreTypes(False, True, False)
        self.rtmidi.closePort()
        for i in range(self.rtmidi.getPortCount()):
            self.rtmidi.getPortName(i)
        
    def test_blocking(self):
        """ test blocking reads. """
        self.rtmidi.openPort(0, True)
        print 'move a MIDI device to send some data...'
        m1 = self.rtmidi.getMessage()
        m2 = self.rtmidi.getMessage()
        m3 = self.rtmidi.getMessage()
        self.rtmidi.closePort()

    def test_non_blocking(self):
        """ test non-blocking reads. """
        self.rtmidi.openPort(1)
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.closePort()
    
import time
class RtMidiOutTest(unittest.TestCase):
    def setUp(self):
        self.rtmidi = rtmidi.RtMidiOut()

    def test_00_openVirtual(self):
        vi = rtmidi.RtMidiOut()
        vi.openVirtualPort('myport')
        while 1:
#            print 'sending ',
#            sys.stdout.flush()
            vi.sendMessage(0xF8)
            time.sleep(.016)
        vi.closePort()

    def test_01_outputs_exist(self):
        self.assertEqual(self.rtmidi.getPortCount() > 0, True)

    def test_funcs(self):
        """ test that certain functions can be called. """
        self.rtmidi.openPort(1)
        self.rtmidi.closePort()

        self.rtmidi.openVirtualPort()
        for i in range(self.rtmidi.getPortCount()):
            self.rtmidi.getPortName(i)


def print_ports(device):

    ports = range(device.getPortCount())
    if ports:
        for i in ports:
            print 'MIDI IN:',device.getPortName(i)
    else:
        print 'NO MIDI PORTS!'


if __name__ == '__main__':
    #print_ports(rtmidi.RtMidiIn())
    #print_ports(rtmidi.RtMidiOut())
    unittest.main()
