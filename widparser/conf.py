import cwiid

translate = {
    'Wiimote.A': cwiid.BTN_A,
    'Wiimote.B': cwiid.BTN_B,
    'Wiimote.Left': cwiid.BTN_LEFT,
    'Wiimote.Right':cwiid.BTN_LEFT,
    'Wiimote.Up': cwiid.BTN_UP,
    'Wiimote.Down': cwiid.BTN_DOWN,
    'Wiimote.Home': cwiid.BTN_HOME,
    'Nunchuk.C': cwiid.NUNCHUK_BTN_C,
}

translamidi = {
    0x90: 'NOTE_ON',
    0x80: 'NOTE_OFF',
}

class Conf():
#    class ButtonMap:
#        def __init__(self):
#            self.bmap = {}
#            
#        def add(btn):
#            
#            
#        def get_action(btn_code):
#            for btn in self.bmap:
#                if btn.code = btn_code:
#                    return btn.action
#            return None

    def __init__(self):
        self.rptmode = 0
        self.wiimote_bmap = {}
        self.nunchuk_bmap = {}
        #self.axis = AxisMap()

    def add_btn(self, btn):
        if isinstance(btn, WiimoteButton):
            self.rptmode |= cwiid.RPT_BTN
            self.wiimote_bmap[btn.code] = btn
        elif isinstance(btn, NunchukButton):
            self.rptmode |= cwiid.RPT_NUNCHUK
            self.nunchuk_bmap[btn.code] = btn
            
    def add_axis(self, btn, action, func=lambda x, y: x, *args):
        pass

    """
    #FIXME: This is useless now
    def __contains__(self, btn):
        def in_bmap (btn, bmap):
            for item in bmap:
                if item == btn:
                    return True
            return False
        
        if isinstance(btn, WiimoteButton):
            return in_bmap(btn, self.wiimote_bmap.values())
        elif isinstance(btn, NunchukButton):
            return in_bmap(btn, self.nunchuk_bmap.values())        
        else:
            return False
    """
                
class Button():
    codes = ()
    assert_mesg = 'No Button code'
    
    def __init__(self, code=None):
        btncode = translate[code]
        assert btncode in self.codes, assert_mesg
        self.code = btncode
        self.press_action = None
        self.press_modif = lambda x, y: x
        self.press_modif_args = None
        self.release_action = None
        self.release_modif = lambda x, y: x
        self.release_modif_args = None

    def set_press_action(self, action, func=lambda x, y: x, args=None):
        self.press_action = action
        self.press_modif = func
        self.press_modif_args = args

    def set_release_action(self, action, func=lambda x, y: x, args=None):
        self.release_action = action
        self.release_modif = func
        self.release_modif_args = args

    def get_press_action(self):
        if self.press_action:
            return self.press_modif(self.press_action, self.press_modif_args)
        else:
            raise 'Not press action defined for button', self.code    

    def get_release_action(self):
        if self.release_action:
            return self.release_modif(self.release_action, 
                self.release_modif_args)
        else:
            raise 'Not release action defined for button', self.code    

    def __eq__(self, btn):
        return self.code == btn.code

    def __repr__(self):
        return 'btn:%s = Press %s(midi(%s), %s), Release %s(midi(%s), %s)' % \
            (self.code, self.press_modif.__name__, repr(self.press_action), 
                self.press_modif_args, self.release_modif.__name__, 
                repr(self.release_action), self.release_modif_args)

class WiimoteButton(Button):
    codes = (
        cwiid.BTN_A, cwiid.BTN_B, 
        cwiid.BTN_UP, cwiid.BTN_DOWN, cwiid.BTN_LEFT, cwiid.BTN_RIGHT,
        cwiid.BTN_MINUS, cwiid.BTN_HOME, cwiid.BTN_PLUS,
        cwiid.BTN_1, cwiid.BTN_2
    )
    assert_mesg = 'Not Wiimote Button code'

    def __eq__(self, btn):
        if not isinstance(btn, WiimoteButton): 
            return False
        return self.code == btn.code

class NunchukButton(Button):
    codes = (cwiid.NUNCHUK_BTN_C, cwiid.NUNCHUK_BTN_Z)
    assert_mesg = 'Not Nunchuk Button code'

    def __eq__(self, btn):
        if not isinstance(btn, NunchukButton): 
            return False
        return self.code == btn.code

#TODO: Some kind of pattern may be applied
class MidiMesg():
    def __init__(self, status, data1, data2=None):
        self.status = status
        self.data1 = data1
        self.data2 = data2

    @property
    def reversible(self):
        return False

    def __repr__(self):
        return '%x, %d, %d' % (self.status, self.data1, self.data2)

class ReversibleMidiMesg(MidiMesg):
    def __init__(self, status, data1, data2=None):
        MidiMesg.__init__(self, status, data1, data2)

    @property
    def reversible(self):
        return True
        
class Note(ReversibleMidiMesg):
    def __init__(self, key, velocity=127, channel=0):
        assert channel >=0 and channel < 15, 'Only 16 channel are available'
        self.channel = channel
        MidiMesg.__init__(self, 0x90+self.channel, key, velocity)

    def __neg__(self):
        return MidiMesg(0x80+self.channel, self.data1, self.data2)

    def __repr__(self):
        return '%s(%d, %d, %d)' % (translamidi[self.status], self.data1, 
            self.data2, self.channel)
