#!/usr/bin/python

import math

import pypm

from wiiasynclib import WiimoteDevice
from widparser import WidParser
from widparser.control import ButtonSet


LATENCY = 100

def convert(value, factor, scale):
    new = scale*(value+factor)/(2*factor)
    return int(new)
    
class WiiMidi():
    def __init__(self):
        self.last = {'wii_btn': ButtonSet(), 'roll': 0, 'pitch': 0}
        self.midiout = pypm.Output(pypm.GetDefaultOutputDeviceID(), LATENCY)

    @staticmethod
    def is_pressed(btncode, pressed):
        return (btncode & pressed) == btncode

    def send_midi(self, midi):
        data = tuple([x for x in [midi.status, midi.data1, midi.data2] if x])
        self.midiout.WriteShort(*data)
    
    def process_btn(self, wiidevice, mesg_btn, btnmap):
        current = self.last['wii_btn']
        
        #Check for new pressed buttons and send the associated midi messages
        for button in [btn for btn in btnmap.sensitive_buttons(mesg_btn) \
                if not btn in self.last['wii_btn'] and \
                self.is_pressed(btn.btncode, mesg_btn)]:
            current.add(button)
            if button.press_action:
                self.send_midi(button.get_press_action())

        #Check for new released buttons and send the associated midi messages
        for button in [btn for btn in self.last['wii_btn'] \
                if not self.is_pressed(btn.btncode, mesg_btn)]:
            current.remove(button)
            if button.release_action:
                self.send_midi(button.get_release_action())
       
        self.last['wii_btn'] = current

    def process_acc(self, wiidevice, mesg_acc, axis):
        axis.set_acc(mesg_acc)
        
        roll = convert(axis.roll, math.pi, 127)
        pitch = convert(axis.pitch, 1.55, 16)
        
        if roll != self.last['roll']:
            self.last['roll'] = roll
            self.midiout.sendMessage(0xE0, 10, roll)
        
        if pitch != self.last['pitch']:
            self.last['pitch'] = pitch
        
if __name__ == '__main__':
    import sys
    #from widparser.control import Axis
    
    pypm.Initialize()

    parser = WidParser()
    wiidevice = WiimoteDevice()
    wiimidi = WiiMidi()
    
    parser.load(sys.argv[1])

    print 'Put Wiimote in discoverable mode now (press 1+2)'
    wiidevice.associate()
    
    wiidevice.rptmode = parser.conf.rptmode | 4
    #calibration = wiidevice.get_acc_cal(0)
    #wiiaxis = Axis(calibration)
    
    wiidevice.connect('mesg_btn', wiimidi.process_btn, parser.conf.wiimote_bmap)
    #wiidevice.connect('mesg_acc', wiimidi.process_acc, wiiaxis)
