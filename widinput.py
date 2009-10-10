#!/usr/bin/python

from wiiasynclib import WiimoteDevice
from widparser import WidParser
from rtmidi import RtMidiOut

MIDIPORT_NAME = 'WiiMidi'

class WiiMidi():
    def __init__(self):
        self.last = {'mesg_btn': 0}
        self.midiout = RtMidiOut()
        self.midiout.openVirtualPort(MIDIPORT_NAME)
    
    @staticmethod
    def is_pressed(btn, pressed, last_pressed):
         return btn & pressed and not btn & last_pressed

    @staticmethod
    def is_released(btn, pressed, last_pressed):
         return not btn & pressed and btn & last_pressed

    def process_btn(self, wiidevice, mesg_btn, btnmap):
        for button in btnmap.sensible_buttons(mesg_btn):
            #FIXME: It can't process Wiimote.A + Wiimote.B at all!
            if button.press_action and self.is_pressed(button.btncode, 
                    mesg_btn, self.last['mesg_btn']):
                midi = button.get_press_action()
                data = tuple([x for x in [midi.status, midi.data1, midi.data2] \
                            if x])
                self.midiout.sendMessage(*data)

            elif button.release_action and self.is_released(buttonbtncode, 
                    mesg_btn, self.last['mesg_btn']):
                midi = button.get_release_action()
                data = tuple([x for x in [midi.status, midi.data1, midi.data2] \
                            if x])
                self.midiout.sendMessage(*data)

        self.last['mesg_btn'] = mesg_btn

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
