import cwiid
from control import WiimoteButton, NunchukButton

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
