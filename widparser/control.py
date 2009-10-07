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
