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

class ButtonSet():
    def __init__(self):
        self.set = {}

    def add(self, btn):
        assert isinstance(btn, Button), 'Not Button instance'
        self.set[btn.btncode] = btn

    def remove(self, btn):
        assert isinstance(btn, Button), 'Not Button instance'
        del self.set[btn.btncode]

    def sensible_buttons(self, mesg_btn):
        #TODO: Maybe it's better a sorted insert on ButtonSet
        sorted_btncodes = self.set.keys()
        sorted_btncodes.sort()
        sorted_btncodes.reverse()
        
        for btn in [self.set[btncode] for btncode in sorted_btncodes]:
            if btn.btncode & mesg_btn:
                mesg_btn -= btn.btncode
                yield btn

    def __iter__(self):
        return self.set.values().__iter__()

    def __contains__(self, btn):
        return btn in self.set.values()

    def __repr__(self):
        return 'ButtonSet(%s)' % repr([repr(x) for x in self.set.values()])

class Button():
    codes = ()
    assert_mesg = 'No Button code'
    
    def __init__(self, btncode):
        if not type(btncode) == list:
            self._code = [btncode]
        #FIXME: better type checking it's needed
        else:
            self._code = btncode
            
        #TODO: Maybe a code this ala @property makes it clever
        self.press_action = None
        self.press_modif = lambda x, y: x
        self.press_modif_args = None
        self.release_action = None
        self.release_modif = lambda x, y: x
        self.release_modif_args = None
        
    @property
    def btncode(self):
        result = 0
        for code in self._code:
            result |= translate[code]
        return result

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
            (self.btncode, self.press_modif.__name__, repr(self.press_action), 
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

    def __eq__(self, wiibtn):
        if not isinstance(wiibtn, WiimoteButton): 
            return False
        return self.btncode == wiibtn.btncode

    def __add__(self, wiibtn):
        if self == wiibtn:
            return wiibtn
        else:
            return WiimoteButton(self._code + wiibtn._code)

class NunchukButton(Button):
    codes = (cwiid.NUNCHUK_BTN_C, cwiid.NUNCHUK_BTN_Z)
    assert_mesg = 'Not Nunchuk Button code'

    def __eq__(self, nunbtn):
        if not isinstance(nunbtn, NunchukButton): 
            return False
        return self.code == nunbtn.code
        
if __name__ == '__main__':
    from midimesg import Note
    
    a = WiimoteButton('Wiimote.A')
    a.set_press_action(Note(90))
    
    b = WiimoteButton('Wiimote.B')
    b.set_press_action(Note(100))
    
    ab = WiimoteButton('Wiimote.A') + WiimoteButton('Wiimote.B')
    ab.set_press_action(Note(120))
    
    s = ButtonSet()
    s.add(a)
    s.add(b)
    s.add(ab)
    
    for button in s.sensible_buttons(12):
        print button
