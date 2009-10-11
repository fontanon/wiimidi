#!/usr/bin/python

from wiiasynclib import WiimoteDevice
from widparser import WidParser
from widparser.control import ButtonSet
from rtmidi import RtMidiOut

MIDIPORT_NAME = 'WiiMidi'

class WiiMidi():
    def __init__(self):
        self.last = {'wii_btn': ButtonSet()}
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
        
if __name__ == '__main__':
    import sys
    
    parser = WidParser()
    wiidevice = WiimoteDevice()
    wiimidi = WiiMidi()
    
    parser.load(sys.argv[1])
    wiidevice.rptmode = parser.conf.rptmode
    wiidevice.connect('mesg_btn', wiimidi.process_btn, parser.conf.wiimote_bmap)

    print 'Put Wiimote in discoverable mode now (press 1+2)'
    wiidevice.associate()
