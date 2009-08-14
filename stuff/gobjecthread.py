import gobject
import threading
import time
import cwiid
import sys

class WiimoteController(gobject.GObject, threading.Thread):
    __gsignals__ = { 
                       'mesg_recived' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
                       'disconnected' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
                       'error' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
                       'mesg_status' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
                       'mesg_acc' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
                       'mesg_btn' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self, rtp = 6):
        gobject.GObject.__init__(self)
        threading.Thread.__init__(self)

        self.wiimote = cwiid.Wiimote()
        self.wiimote.rpt_mode = rtp
        self.wiimote.led = cwiid.LED1_ON
        self.wiimote.enable(cwiid.FLAG_MESG_IFC)
        self.wiimote.mesg_callback = self.callback

        self.timeToQuit = threading.Event()

    def run(self):
        while not self.timeToQuit.isSet():
            time.sleep(0.05)

    def stop(self):
        self.timeToQuit.set()
        self.join()

    def callback(self, mesg_list):
        self.emit('mesg_recived', mesg_list)

        for mesg in mesg_list: 
            if mesg[0] == cwiid.MESG_ERROR:
                if mesg[1] == cwiid.ERROR_DISCONNECT:
                    self.emit('disconnected', mesg[1])
                else:
                    self.emit('error', mesg[1])
            elif mesg[0] == cwiid.MESG_STATUS:
                self.emit('mesg_status', mesg[1])
            elif mesg[0] == cwiid.MESG_ACC:
                self.emit('mesg_acc', mesg[1])
            elif mesg[0] == cwiid.MESG_BTN:
                self.emit('mesg_btn', mesg[1])
        
gobject.type_register(WiimoteController)

if __name__ == '__main__':
    def print_mesg_list(obj, mesg_list, data=None):
        for mesg in mesg_list:
            print mesg

    def print_mesg(obj, mesg, data=None):
        print data, mesg

    def exit(obj, mesg, data=None):
        obj.stop()
        sys.exit(0)

    gobject.threads_init()

    print "Press 1+2"
    wii = WiimoteController()
    wii.connect('mesg_status', print_mesg, 'status: ')
    wii.connect('mesg_acc', print_mesg, 'acc: ')
    wii.connect('mesg_btn', print_mesg, 'btn: ')
    wii.connect('disconnected', exit)
    wii.start()

    gobject.MainLoop().run()
