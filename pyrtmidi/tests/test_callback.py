import os, sys

BUILD_PATHS = [os.path.join(os.getcwd(), 'build/lib.linux-x86_64-2.4/'),
               os.path.join(os.getcwd(), 'build/lib.darwin-8.5.0-Power_Macintosh-2.3/'),
               os.path.join(os.getcwd(), 'build/lib.darwin-8.8.1-i386-2.3/'),
               os.path.join(os.getcwd(), 'build/lib.darwin-8.11.0-Power_Macintosh-2.3/'),
               ]
sys.path = BUILD_PATHS + sys.path

for i in sys.path: print i

import unittest
import rtmidi
import time

def print_ports(device):
    ports = range(device.getPortCount())
    if ports:
        for i in ports:
            print 'MIDI IN:',device.getPortName(i)
    else:
        print 'NO MIDI PORTS!'

def callback(*args):
    print '>>>', args


def main():
    midiin = rtmidi.RtMidiIn()
    print_ports(midiin)

    for i in range(midiin.getPortCount()):
        midiin.getPortName(i)
        
    midiin.setCallback(callback)
    midiin.openPort(0)

    try:
        while 1:
#            print 'hey'
            time.sleep(.1)
    except KeyboardInterrupt:
        print 'quit'
    midiin.closePort()

if __name__ == '__main__':
    main()
