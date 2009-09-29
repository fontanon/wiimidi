#!/usr/bin/python

import gtk
from gtk import glade
import exceptions
import cwiid
import math

from wiiasynclib import WiimoteDevice

class WmGUI:
    btn_on = gtk.gdk.color_parse('green')
    btn_off = gtk.gdk.color_parse('grey')

    def __init__(self):
        self.wTree = glade.XML('wmgui.glade', None, None)
        dic = {'connectbutton_toggled_cb':self.connectbutton_toggled_cb,
               'btncheck_toggled_cb':self.rptmode_toggled_cb,
               'accdatacheck_toggled_cb':self.rptmode_toggled_cb,
               'irdatacheck_toggled_cb':self.rptmode_toggled_cb,
               'extensiondata_toggled_cb':self.rptmode_toggled_cb,
               'rumblecheck_toggled_cb':self.rumblecheck_toggled_cb,
               'led1check_toggled_cb':self.calculate_led_cb,
               'led2check_toggled_cb':self.calculate_led_cb,
               'led3check_toggled_cb':self.calculate_led_cb,
               'led4check_toggled_cb':self.calculate_led_cb}
        self.wTree.signal_autoconnect(dic)
        self.wTree.signal_connect('wmgui_window_destroy_cb', self.main_quit) 
        self.wTree.signal_connect('quitmenuitem_activate_cb', self.main_quit) 

        self.wmguiwindow = self.wTree.get_widget('wmguiwindow')
        self.connectbutton = self.wTree.get_widget('connectbutton')

        self.btncheck = self.wTree.get_widget('btncheck')
        self.accdatacheck = self.wTree.get_widget('accdatacheck')
        self.irdatacheck = self.wTree.get_widget('irdatacheck')
        self.extensiondatacheck = self.wTree.get_widget('extensiondatacheck')
        self.rumblecheck = self.wTree.get_widget('rumblecheck')
        self.led1check = self.wTree.get_widget('led1check')
        self.led2check = self.wTree.get_widget('led2check')
        self.led3check = self.wTree.get_widget('led3check')
        self.led4check = self.wTree.get_widget('led4check')
        self.upevbox = self.wTree.get_widget('upevbox')
        self.downevbox = self.wTree.get_widget('downevbox')
        self.leftevbox = self.wTree.get_widget('leftevbox')
        self.rightevbox = self.wTree.get_widget('rightevbox')
        self.abtnevbox = self.wTree.get_widget('abtnevbox')
        self.bbtnevbox = self.wTree.get_widget('bbtnevbox')
        self.minusevbox = self.wTree.get_widget('minusevbox')
        self.homeevbox = self.wTree.get_widget('homeevbox')
        self.plusevbox = self.wTree.get_widget('plusevbox')
        self.oneevbox = self.wTree.get_widget('oneevbox')
        self.twoevbox = self.wTree.get_widget('twoevbox')
        self.progAccX = self.wTree.get_widget('progAccX')
        self.progAccY = self.wTree.get_widget('progAccY')
        self.progAccZ = self.wTree.get_widget('progAccZ')

        self.wiimote = WiimoteDevice()
        self.wiimote.rptmode = 0
        self.wiimote.connect('mesg_btn', self.btn_cb)
        self.wiimote.connect('mesg_acc', self.acc_cb)


    def main_quit(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        gtk.main_quit()

    def connectbutton_toggled_cb(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        else:
            msg = "Put Wiimote in discoverable mode (press 1+2) and close me"
            dlg = gtk.MessageDialog(self.wmguiwindow, gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, msg)
            dlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
            dlg.run()

            try:
                self.wiimote.associate()
            except exceptions.Exception, err:
                #FIXME: I think there must be a better way to block handler
                self.connectbutton.handler_block_by_func(self.connectbutton_toggled_cb)
                self.connectbutton.set_active(False)
                self.connectbutton.handler_unblock_by_func(self.connectbutton_toggled_cb)
                errdlg = gtk.MessageDialog(self.wmguiwindow, gtk.DIALOG_MODAL, 
                        gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, str(err.args))
                errdlg.run()
                errdlg.destroy()
            finally:
                dlg.destroy()

        #FIXME: This sucks!
        self.wm_cal_zero, self.wm_cal_one = self.wiimote.get_acc_cal(cwiid.EXT_NONE)

    def btn_cb(self, wiimote, mesg):
        gtk.gdk.threads_enter() #This prevent for gui crashes
        self.upevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_UP) and self.btn_on or self.btn_off)
        self.downevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_DOWN) and self.btn_on or self.btn_off)
        self.leftevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_LEFT) and self.btn_on or self.btn_off)
        self.rightevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_RIGHT) and self.btn_on or self.btn_off)
        self.abtnevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_A) and self.btn_on or self.btn_off)
        self.bbtnevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_B) and self.btn_on or self.btn_off)
        self.minusevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_MINUS) and self.btn_on or self.btn_off)
        self.homeevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_HOME) and self.btn_on or self.btn_off)
        self.plusevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_PLUS) and self.btn_on or self.btn_off)
        self.oneevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_1) and self.btn_on or self.btn_off)
        self.twoevbox.modify_bg(gtk.STATE_NORMAL, 
                (mesg & cwiid.BTN_2) and self.btn_on or self.btn_off)
        gtk.gdk.threads_leave() #This prevent for gui crashes

    def acc_cb(self, wiimote, mesg):
        gtk.gdk.threads_enter() #This prevent for gui crashes
        self.progAccX.set_fraction(float(mesg[0])/0xFF)
        self.progAccY.set_fraction(float(mesg[1])/0xFF)
        self.progAccZ.set_fraction(float(mesg[2])/0xFF)
        gtk.gdk.threads_leave() #This prevent for gui crashes

        acc = [(float(mesg[i]) - self.wm_cal_zero[i]) /  \
                (self.wm_cal_one[i] - self.wm_cal_zero[i]) \
                for i in (cwiid.X, cwiid.Y, cwiid.Z)]

        a = math.sqrt(sum(map(lambda x: x**2, acc)))

        try:
            roll = math.atan(acc[cwiid.X]/acc[cwiid.Z])
            if acc[cwiid.Z] <= 0:
                if acc[cwiid.X] > 0: 
                    roll += math.pi
                else: 
                    roll -= math.pi

            pitch = math.atan(acc[cwiid.Y]/acc[cwiid.Z]*math.cos(roll))
        except:
            #TODO: Why sometimes acc[2] it's zero ?
            print acc, mesg, self.wm_cal_zero

    def rptmode_toggled_cb(self, obj):
        self.wiimote.rptmode = (self.btncheck.get_active() and cwiid.RPT_BTN) \
                ^ (self.accdatacheck.get_active() and cwiid.RPT_ACC) \
                ^ (self.irdatacheck.get_active() and cwiid.RPT_IR) \
                ^ (self.extensiondatacheck.get_active() and cwiid.RPT_EXT)

    def calculate_led_cb(self, obj):
        self.wiimote.led = ((self.led1check.get_active() and cwiid.LED1_ON) \
                ^ (self.led2check.get_active() and cwiid.LED2_ON) \
                ^ (self.led3check.get_active() and cwiid.LED3_ON) \
                ^ (self.led4check.get_active() and cwiid.LED4_ON))

    def rumblecheck_toggled_cb(self, check):
        self.wiimote.rumble = check.get_active()

if __name__ == '__main__':
    gtk.gdk.threads_init()
    wmgui = WmGUI()
    gtk.main()
