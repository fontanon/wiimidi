# pywiimote-control: a tiny modular wiimote remote control application
# Copyright (C) 2008 Luca Greco <rpl@salug.it>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cwiid
import sys
import rtmidi
import math

CHORD = 70
MidiOut = None
valor2, valor, control = 0, 0, 0

NEW_AMOUNT = 0.1
OLD_AMOUNT = 1 - NEW_AMOUNT

acc = [0,0,0]
max_roll, max_pitch, max_acc = 0,0,0
min_roll, min_pitch, min_acc = 0,0,1
old_valor2 = 0

def init(zero, one):
    global MidiOut, acc_zero, acc_one
    MidiOut = rtmidi.RtMidiOut()
    MidiOut.openVirtualPort('Wii')
    acc_zero = zero
    acc_one = one

def close ():
    global MidiOut
    MidiOut.closePort()

def callback(mesg):
    def convert(value, factor, scale):
        new = scale*(value+factor)/(2*factor)
        return int(new)
    
    global MidiOut, control, valor, valor2, acc_zero, acc_one, acc
    global max_roll, max_pitch, max_acc
    global min_roll, min_pitch, min_acc
    global old_valor2

    if MidiOut == None:
       return

    if mesg[0] == cwiid.MESG_BTN:
        #print cwiid.BTN_A, cwiid.BTN_B, cwiid.BTN_A ^ cwiid.BTN_B, mesg
        if mesg[1] == cwiid.BTN_A:
            MidiOut.sendMessage(0x90,CHORD,100)
        elif mesg[1] == cwiid.BTN_B:
            MidiOut.sendMessage(0x90,CHORD+5,100)
        elif mesg[1] == cwiid.BTN_B ^ cwiid.BTN_A:
            MidiOut.sendMessage(0x90,CHORD+10,100)
        elif mesg[1] == cwiid.BTN_RIGHT:
            control += 1
            MidiOut.sendMessage(0xB0, control, valor)
            print control
        elif mesg[1] == cwiid.BTN_LEFT:
            control -= 1
            MidiOut.sendMessage(0xB0, control, valor)
            print control
        elif mesg[1] == cwiid.BTN_DOWN:
            control -= 10
            MidiOut.sendMessage(0xB0, control, valor)
            print control
        elif mesg[1] == cwiid.BTN_UP:
            control += 10
            MidiOut.sendMessage(0xB0, control, valor)
            print control
        else:
            MidiOut.sendMessage(0x80,CHORD,0)
            MidiOut.sendMessage(0x80,CHORD+5,0)
            MidiOut.sendMessage(0x80,CHORD+10,0)
    elif mesg[0] == cwiid.MESG_ACC:
        #import pdb; pdb.set_trace()
        acc = [NEW_AMOUNT*(new-zero)/(one-zero) + OLD_AMOUNT*old 
                for old,new,zero,one in zip(acc,mesg[1],acc_zero,acc_one)]
        a = math.sqrt(sum(map(lambda x: x**2, acc)))
        roll = math.atan(acc[cwiid.X]/acc[cwiid.Z])
        if acc[cwiid.Z] <= 0:
            if acc[cwiid.X] > 0: roll += math.pi
            else: roll -= math.pi
        pitch = math.atan(acc[cwiid.Y]/acc[cwiid.Z]*math.cos(roll))
        """
        print "mesg", mesg
        print "acc: ", acc
        print "a: ", a
        print "roll: ", roll
        print "pitch: ", pitch
        """
        #import pdb; pdb.set_trace()
        if roll > max_roll: max_roll = roll
        if pitch > max_pitch: max_pitch = pitch
        if a > max_acc: max_acc = a
 
        if roll < min_roll: min_roll = roll
        if pitch < min_pitch: min_pitch = pitch
        if a < min_acc: min_acc = a
        
        valor = convert(roll, math.pi, 127)
        valor2 = convert(pitch, 1.55, 16)
        
        """
        print "CUR: ", a, roll, pitch
        print "MAX: ", max_acc, max_roll, max_pitch
        print "MIN: ", min_acc, min_roll, min_pitch
        print roll, valor
        print pitch, valor2
        """
        #MidiOut.sendMessage(0xB0, control, convert(valor))
        MidiOut.sendMessage(0xE0, 10, valor)
        if valor2 != old_valor2:
            print "cambio: ", old_valor2, valor2
            MidiOut.sendMessage(0x90, valor2+100, 100)
            old_valor2 = valor2
