#!/usr/bin/python

import math
import time

import cwiid
import rtmidi

class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if '__instance' not in vars(cls):
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

class WiiStatus(Singleton):
    NEW_AMOUNT = 0.1
    OLD_AMOUNT = 1 - NEW_AMOUNT
    acc = [0,0,0]
    acc_zero = [0,0,0]
    acc_one = [0,0,0]
    pitch = None
    roll = None
    a = None

    __instance = None

    def calc(self, acc):
        self.acc = [self.NEW_AMOUNT*(new-zero)/(one-zero) + self.OLD_AMOUNT*old 
                for old,new,zero,one in zip(self.acc, acc, self.acc_zero, 
                    self.acc_one)]
        self.a = math.sqrt(sum(map(lambda x: x**2, self.acc)))
        self.roll = math.atan(self.acc[cwiid.X]/self.acc[cwiid.Z])
        if self.acc[cwiid.Z] <= 0:
            if self.acc[cwiid.X] > 0: self.roll += math.pi
            else: self.roll -= math.pi
        self.pitch = math.atan(self.acc[cwiid.Y]/self.acc[cwiid.Z]*math.cos(self.roll))
        return self.a, self.roll, self.pitch

wiistatus = WiiStatus()

def callback(mesg_list):
    def convert(value, factor, scale):
        new = scale*(value+factor)/(2*factor)
        return int(new)

    def convert2(value, factor, scale):
        new = scale*value/(2*factor)
        return int(new)

    for mesg in mesg_list:
        if mesg[0] == cwiid.MESG_ACC:
            a, roll, pitch = wiistatus.calc(mesg[1])
            valor = convert2(roll, math.pi, 4)
            valor2 = convert2(pitch, 1.55, 4)
            print valor, valor2

if __name__ == '__main__':
    print 'Put Wiimote in discoverable mode now (press 1+2)'
    wiimote = cwiid.Wiimote()
    wiimote.rpt_mode = cwiid.RPT_BTN ^ cwiid.RPT_ACC 
    wiimote.led = cwiid.LED1_ON
    wiimote.enable(cwiid.FLAG_MESG_IFC)

    wiistatus.acc_zero, wiistatus.acc_one = wiimote.get_acc_cal(cwiid.EXT_NONE)
    wiimote.mesg_callback = callback

    while 1:
        time.sleep(0.05)
