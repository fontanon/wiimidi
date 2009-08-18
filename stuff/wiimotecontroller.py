import gobject
import threading
import exceptions
import time
import cwiid

from utils import simple_decorator

SLEEP_TIME = 0.05

RPT_MODE = cwiid.RPT_BTN | cwiid.RPT_ACC
LED = 0
RUMBLE = False
FLAG = cwiid.FLAG_MESG_IFC

@simple_decorator
def is_associated(func):
    def perform (self, *args, **kwargs):
        if self.associated:
            return func(self, *args, **kwargs)
        else:
            raise gobject.GError('Wiimote not associated yet')
    return perform

class CwiidLauncher(threading.Thread):
    def __init__(self, callback_func, btaddr=''):
        threading.Thread.__init__(self)

        self.timeToQuit = threading.Event()

        self.wiiobj = cwiid.Wiimote(btaddr)
        self.wiiobj.mesg_callback = callback_func

    def run(self):
        while not self.timeToQuit.isSet():
            time.sleep(SLEEP_TIME)

    def stop(self):
        self.wiiobj.close()
        self.timeToQuit.set()
        self.join()

class WiimoteDevice(gobject.GObject):
    __gsignals__ = {
            'mesg_any' : (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_status' : (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_acc' :    (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_btn' :    (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_ir' :     (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_nunchuk' : (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'mesg_classic' : (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'associated' :   (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
            'error' : (gobject.SIGNAL_RUN_LAST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
    }

    rptmode = gobject.property(type=gobject.TYPE_INT, default=RPT_MODE,
            minimum=0, maximum=127, 
            nick='rptmode', blurb='Wiimote report mode')

    led = gobject.property(type=gobject.TYPE_INT, default=LED,
            minimum=0, maximum=15, 
            nick='led', blurb='Wiimote led state')

    rumble = gobject.property(type=gobject.TYPE_BOOLEAN, default=RUMBLE,
            nick='rumble', blurb='Wiimote rumble state')

    @gobject.property
    @is_associated 
    def state(self, type=gobject.TYPE_PYOBJECT, nick='state', 
            blurb='Wiimote global state'):
        return self.wiidevice.wiiobj.state

    @gobject.property
    def associated(self, type=gobject.TYPE_BOOLEAN,
            nick='associated', blurb='Shows if wiimote it\'s associated'):
        return self.__associated

    def __init__(self):
        gobject.GObject.__init__(self)
        self.wiidevice = None
        self.__associated = False

    #FIXME: Only on dissociated state
    def associate(self, btaddr=''):
        def setup(wiimote, rptmode=6, led=0, rumble=0):
            wiimote.rpt_mode = rptmode
            wiimote.led = led
            wiimote.rumble = rumble
            #FIXME: This need to be gobjetized in some way
            wiimote.enable(FLAG)

        try:
            self.wiidevice = CwiidLauncher(self.callback, btaddr)
            setup(self.wiidevice.wiiobj, self.rptmode, self.led, self.rumble)
        except exceptions.Exception, e:
            raise gobject.GError(e)
            return False

        self.connect('notify::rptmode', self.__rptmode_cb)
        self.connect('notify::led', self.__led_cb)
        self.connect('notify::rumble', self.__rumble_cb)

        self.wiidevice.start()
        self.__associated = True
        self.emit('associated', True)

        return True

    @is_associated
    def dissociate(self):
        self.wiidevice.stop()
        self.wiidevice = None
        self.__associated = False
        self.emit('associated', False)

    def callback(self, mesg_list):
        self.emit('mesg_any', mesg_list)

        for mesg in mesg_list: 
            if mesg[0] == cwiid.MESG_ERROR:
                if mesg[1] == cwiid.ERROR_DISCONNECT:
                    self.dissociate()
                else:
                    self.emit('error', mesg[1])
            elif mesg[0] == cwiid.MESG_STATUS:
                self.emit('mesg_status', mesg[1])
            elif mesg[0] == cwiid.MESG_ACC:
                self.emit('mesg_acc', mesg[1])
            elif mesg[0] == cwiid.MESG_BTN:
                self.emit('mesg_btn', mesg[1])
            elif mesg[0] == cwiid.MESG_IR:
                self.emit('mesg_ir', mesg[1])
            elif mesg[0] == cwiid.MESG_NUNCHUK:
                self.emit('mesg_nunchuk', mesg[1])
            elif mesg[0] == cwiid.MESG_CLASSIC:
                self.emit('mesg_classic', mesg[1])

    @is_associated
    def enable(self, flag):
        self.wiidevice.wiiobj.enable(flag)

    @is_associated
    def read(flags, offset, len):
        return self.wiidevice.wiiobj.read(flags, offset, len)

    @is_associated
    def write(flags, offset, buffer):
        self.wiidevice.wiiobj.write(flags, offset, buffer)

    def __rumble_cb(self, obj, prop):
        self.wiidevice.wiiobj.rumble = obj.get_property('rumble')

    def __rptmode_cb(self, obj, prop):
        self.wiidevice.wiiobj.rpt_mode = obj.get_property('rptmode')

    def __led_cb(self, obj, prop):
        self.wiidevice.wiiobj.led = obj.get_property('led')

gobject.type_register(WiimoteDevice)

if __name__ == '__main__':
    import sys

    def print_mesg_list(obj, mesg_list, data=None):
        for mesg in mesg_list:
            print mesg

    def print_mesg(obj, mesg, data=None):
        print data, mesg

    def associate_status(obj, associated, data=None):
        if associated:
            print "Wiimote associated succesfuly"
        else:
            print "Wiimote dissociated"
            sys.exit(0)

    def stop_rumble(obj):
        obj.rumble = 0

    def process_acc(obj):
        obj.rptmode = cwiid.RPT_BTN | cwiid.RPT_ACC

    def stop(obj):
        obj.dissociate()

    gobject.threads_init()

    print 'Put Wiimote in discoverable mode now (press 1+2)'
    wii = WiimoteDevice()
    wii.rptmode = cwiid.RPT_BTN
    wii.led = cwiid.LED1_ON
    wii.rumble = True
    wii.connect('mesg_status', print_mesg, 'status: ')
    wii.connect('mesg_acc', print_mesg, 'acc: ')
    wii.connect('mesg_btn', print_mesg, 'btn: ')
    wii.connect('associated', associate_status)
    wii.associate()

    gobject.timeout_add(2000, stop_rumble, wii)
    gobject.timeout_add(5000, process_acc, wii)
    gobject.timeout_add(7000, stop, wii)
    gobject.MainLoop().run()
