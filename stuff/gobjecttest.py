import gobject 
import time
import cwiid

class WiimoteController(gobject.GObject):
    __gsignals__ = { 
                       'mesg_recived' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,))
                       'disconnected' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,))
                       'error' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, rtp = 6):
        gobject.GObject.__init__(self)
        print "Press 1+2"
        wiimote = cwiid.Wiimote()
        wiimote.rpt_mode = rtp
        wiimote.led = cwiid.LED1_ON
        wiimote.enable(cwiid.FLAG_MESG_IFC)
        wiimote.mesg_callback = self.callback
        self.wiimote = wiimote
        
    def callback(self, mesg_list):
        self.emit('mesg_recived', mesg_list)

        for mesg in mesg_list: 
            if mesg[0] == cwiid.MESG_ERROR:
                if mesg[1] == cwiid.ERROR_DISCONNECT:
                    print "Wiimote disconnected!!"
                    self.emit('disconnected', mesg[0])
                else:
                    self.emit('error', mesg[0])
            elif mesg[0] == cwiid.MESG_ACC:
                self._acc_control(mesg[1], 0)
            elif mesg[0] == cwiid.MESG_BTN:
                self._btn_control(mesg[1], 0)
        
gobject.type_register(WiimoteController)

if __name__ == '__main__':
    def print_mesg_list(obj, mesg_list, data=None):
        for mesg in mesg_list:
            print mesg

    wii = WiimoteController()
    wii.connect('mesg_recived', print_mesg_list)

    while True:
        time.sleep(0.5)
