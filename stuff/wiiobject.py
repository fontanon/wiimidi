import gobject
import threading
import time
import cwiid

SLEEP_TIME = 0.05

class WiimoteDevice(threading.Thread):
    def __init__(self, callback_func):
        threading.Thread.__init__(self)
        self.timeToQuit = threading.Event()

        wiimote = cwiid.Wiimote()
        wiimote.rpt_mode = 6
        wiimote.led = cwiid.LED1_ON
        wiimote.enable(cwiid.FLAG_MESG_IFC)
        wiimote.mesg_callback = callback_func

        self.wiiobj = wiimote

    def run(self):
        while not self.timeToQuit.isSet():
            time.sleep(SLEEP_TIME)

    def stop(self):
        self.wiimote.close()
        self.timeToQuit.set()
        self.join()


class WiimoteController(gobject.GObject):
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

    rtp_mode = gobject.property(type=gobject.TYPE_INT, default=6,
            minimum=0, maximum=127, 
            nick='rtp_mode', blurb='Wiimote report mode')
    led = gobject.property(type=gobject.TYPE_INT, default=0,
            minimum=0, maximum=15, 
            nick='led', blurb='Wiimote led state')
    rumble = gobject.property(type=gobject.TYPE_BOOLEAN, default=False,
            nick='rumble', blurb='Wiimote rumble state')

    def __init__(self):
        gobject.GObject.__init__(self)
        self.wiidevice = WiimoteDevice(self.callback)

    def start(self):
        self.wiidevice.start()

    def stop(self):
        self.wiidevice.stop()

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
    import sys

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
