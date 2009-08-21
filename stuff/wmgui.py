#!/usr/bin/python

import gtk
from gtk import glade
import cwiid

from wiimotecontroller import WiimoteDevice

class WmGUI:
    def __init__(self):
        self.wTree = glade.XML('wmgui.glade', None, None)
        dic = {'connectbutton_toggled_cb':self.connectbutton_toggled_cb,
               'accdatacheck_toggled_cb':self.accdatacheck_toggled_cb,
               'irdatacheck_toggled_cb':self.irdatacheck_toggled_cb,
               'extensiondata_toggled_cb':self.extensiondata_toggled_cb,
               'rumblecheck_toggled_cb':self.rumblecheck_toggled_cb,
               'led1check_toggled_cb':self.led1check_toggled_cb,
               'led2check_toggled_cb':self.led2check_toggled_cb,
               'led3check_toggled_cb':self.led3check_toggled_cb,
               'led4check_toggled_cb':self.led4check_toggled_cb}
        self.wTree.signal_autoconnect(dic)
        self.wTree.signal_connect('wmgui_window_destroy_cb', self.main_quit) 
        self.wTree.signal_connect('quitmenuitem_activate_cb', self.main_quit) 

        self.wmguiwindow = self.wTree.get_widget('wmguiwindow')
        self.connectbutton = self.wTree.get_widget('connectbutton')

        self.accdatacheck = self.wTree.get_widget('accdatacheck')
        self.irdatacheck = self.wTree.get_widget('irdatacheck')
        self.extensiondatacheck = self.wTree.get_widget('extensiondatacheck')
        self.rumblecheck = self.wTree.get_widget('rumblecheck')
        self.led1check = self.wTree.get_widget('led1check')
        self.led2check = self.wTree.get_widget('led2check')
        self.led3check = self.wTree.get_widget('led3check')
        self.led4check = self.wTree.get_widget('led4check')

        self.wiimote = WiimoteDevice()
        self.wiimote.rptmode = cwiid.RPT_BTN

    def main_quit(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        gtk.main_quit()

    def __set_sensible_ctrls(self, value=True):
        self.accdatacheck.set_sensitive(value)
        self.irdatacheck.set_sensitive(value)
        self.extensiondatacheck.set_sensitive(value)
        self.rumblecheck.set_sensitive(value)
        self.led1check.set_sensitive(value)
        self.led2check.set_sensitive(value)
        self.led3check.set_sensitive(value)
        self.led4check.set_sensitive(value)

    def connectbutton_toggled_cb(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        else:
            msg = "Put Wiimote in discoverable mode now (press 1+2)"
            dlg = gtk.MessageDialog(self.wmguiwindow, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                gtk.BUTTONS_NONE, msg)
            dlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
            dlg.run()

            try:
                self.wiimote.associate()
                self.__set_sensible_ctrls(True)
            except:
                #FIXME: This callback the connectbutton_toggled_cb again!!
                self.connectbutton.set_active(False)
            finally:
                dlg.destroy()

    def accdatacheck_toggled_cb(self, obj):
        pass

    def irdatacheck_toggled_cb(self, obj):
        pass

    def extensiondata_toggled_cb(self, obj):
        pass

    def rumblecheck_toggled_cb(self, check):
        self.wiimote.rumble = check.get_active()

    def led1check_toggled_cb(self, check):
        self.wiimote.led = not check.get_active() or cwiid.LED1_ON

    def led2check_toggled_cb(self, check):
        self.wiimote.led = not check.get_active() or cwiid.LED2_ON

    def led3check_toggled_cb(self, check):
        self.wiimote.led = not check.get_active() or cwiid.LED3_ON

    def led4check_toggled_cb(self, check):
        self.wiimote.led = not check.get_active() or cwiid.LED4_ON

if __name__ == '__main__':
   wmgui = WmGUI()
   gtk.main()
