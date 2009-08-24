#!/usr/bin/python

import gtk
from gtk import glade
import exceptions
import cwiid

from wiimotecontroller import WiimoteDevice

class test:
    btn_on = gtk.gdk.color_parse("green")
    btn_off = gtk.gdk.color_parse("grey")

    def __init__(self):
        self.wTree = glade.XML('gtktest.glade', None, None)
        dic = {'btnconnect_toggled_cb':self.btnconnect_toggled_cb}
        self.wTree.signal_autoconnect(dic)
        self.wTree.signal_connect('dlgwii_close_cb', self.main_quit) 
        self.wTree.signal_connect('btnclose_activate_cb', self.main_quit) 
    
        self.mainwindow = self.wTree.get_widget('dlgwii')
        self.connectbutton = self.wTree.get_widget('btnconnect')

        self.lblacc = self.wTree.get_widget('lblacc')
        self.lblbtn = self.wTree.get_widget('lblbtn')

        self.wiimote = WiimoteDevice()
        self.wiimote.rptmode = cwiid.RPT_BTN | cwiid.RPT_ACC
        self.wiimote.connect('mesg_btn', self.btn_cb)
        self.wiimote.connect('mesg_acc', self.acc_cb)
        self.wiimote.connect('associated', self.main_quit)

    def main_quit(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        gtk.main_quit()

    def btnconnect_toggled_cb(self, obj):
        if self.wiimote.associated:
            self.wiimote.dissociate()
        else:
            msg = "Put Wiimote in discoverable mode (press 1+2) and close me"
            dlg = gtk.MessageDialog(self.mainwindow, gtk.DIALOG_MODAL, 
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
                errdlg = gtk.MessageDialog(dlg, gtk.DIALOG_MODAL, 
                        gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, str(err.args))
                errdlg.run()
                errdlg.destroy()
            finally:
                dlg.destroy()

    def btn_cb(self, wiimote, mesg):
        print mesg
        self.lblbtn.set_label('Btn: ' + str(mesg))

    def acc_cb(self, wiimote, mesg):
        print mesg
        self.lblacc.set_label('Acc: ' + str(mesg))

if __name__ == '__main__':
    test = test()
    gtk.main()
