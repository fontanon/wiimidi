#!/usr/bin/python

import cwiid
import math

from wiiasynclib import WiimoteDevice
from widparser import WidParser
from widparser.control import ButtonSet
from rtmidi import RtMidiOut

MIDIPORT_NAME = 'WiiMidi'

def get_acc(cal, mesg_acc):
    cal_zero, cal_one = cal[0], cal[1]
    
    return [(float(mesg_acc[i]) - cal_zero[i]) / \
        (cal_one[i] - cal_zero[i]) \
        for i in (cwiid.X, cwiid.Y, cwiid.Z)]

def get_roll(acc):
    if acc[cwiid.Z] == 0:
        acc[cwiid.Z] = 0.000000000001

    roll = math.atan(acc[cwiid.X]/acc[cwiid.Z])
        
    if acc[cwiid.Z] <= 0:
        if acc[cwiid.X] > 0: 
            roll += math.pi
        else: 
            roll -= math.pi
            
    return roll

def get_pitch(acc, roll):
    return math.atan(acc[cwiid.Y]/acc[cwiid.Z]*math.cos(roll))  

def convert(value, factor, scale):
    new = scale*(value+factor)/(2*factor)
    return int(new)
    
class WiiMidi():
    def __init__(self):
        self.last = {'wii_btn': ButtonSet(), 'roll': 0, 'pitch': 0}
        self.midiout = RtMidiOut()
        self.midiout.openVirtualPort(MIDIPORT_NAME)
    
    @staticmethod
    def is_pressed(btncode, pressed):
        return (btncode & pressed) == btncode

    def send_midi(self, midi):
        data = tuple([x for x in [midi.status, midi.data1, midi.data2] if x])
        self.midiout.sendMessage(*data)
    
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

    def process_acc(self, wiidevice, mesg_acc, cal):
        acc = get_acc(cal, mesg_acc)
        a = math.sqrt(sum(map(lambda x: x**2, acc)))
        roll = get_roll(acc)
        pitch = get_pitch(acc, roll)
        
        roll2 = convert(roll, math.pi, 127)
        pitch2 = convert(pitch, 1.55, 16)
        
        if roll2 != self.last['roll']:
            self.last['roll'] = roll2
            self.midiout.sendMessage(0xE0, 10, convert(roll, math.pi, 127))        
        
        if pitch2 != self.last['pitch']:
            #print pitch2
            self.last['pitch'] = pitch2    
                          
if __name__ == '__main__':
    import sys
    
    parser = WidParser()
    wiidevice = WiimoteDevice()
    wiimidi = WiiMidi()
    
    parser.load(sys.argv[1])

    print 'Put Wiimote in discoverable mode now (press 1+2)'
    wiidevice.associate()
    
    wiidevice.rptmode = parser.conf.rptmode | 4
    calibration = wiidevice.get_acc_cal(0)
    
    wiidevice.connect('mesg_btn', wiimidi.process_btn, parser.conf.wiimote_bmap)
    wiidevice.connect('mesg_acc', wiimidi.process_acc, calibration)
