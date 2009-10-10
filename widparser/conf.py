import cwiid
from control import ButtonSet, WiimoteButton, NunchukButton

class Conf():
    def __init__(self):
        self.rptmode = 0
        self.wiimote_bmap = ButtonSet()
        self.nunchuk_bmap = ButtonSet()
        #TODO:self.axis = AxisSet()

    def add_btn(self, btn):
        if isinstance(btn, WiimoteButton):
            self.rptmode |= cwiid.RPT_BTN
            self.wiimote_bmap.add(btn)
        elif isinstance(btn, NunchukButton):
            self.rptmode |= cwiid.RPT_NUNCHUK
            self.nunchuk_bmap.add(btn)
