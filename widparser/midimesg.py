import copy

translate = {
    0x90: 'NOTE_ON',
    0x80: 'NOTE_OFF',
    0xC0: 'PROG_CHG',
}

class Borg():
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state

class Wrapper():
    def __init__(self, wrapped):
        self._wrapped = wrapped
    
    def __getattr__(self, n):
        return getattr(self._wrapped, n)

#TODO: Some kind of pattern may be applied
class MidiMesg():
    def __init__(self, status, data1, data2=0):
        self.status = status
        self.data1 = data1
        self.data2 = data2
        self.modif = lambda x, y: x
        self.args = None
        
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
        assert channel >=0 and channel < 16, 'Only 16 channel are available'
        self.channel = channel
        MidiMesg.__init__(self, 0x90+self.channel, key, velocity)

    def __neg__(self):
        return MidiMesg(0x80+self.channel, self.data1, self.data2)

    def __repr__(self):
        return '%s(%d, %d, %d)' % (translate[self.status], self.data1, 
            self.data2, self.channel)

class ProgChg(MidiMesg):
    def __init__(self, program, channel=0):
        MidiMesg.__init__(self, 0xC0+channel, program)
        self.channel = channel

    def __repr__(self):
        return '%s(%d, %d, %d)' % (translate[self.status], self.data1,
            self.data2 or 0, self.channel)
     
class Data1Step(Wrapper):
    def __init__(self, midimesg, step):
        Wrapper.__init__(self, midimesg)
        self._step = step
        self._current = self._wrapped.data1

    def data1_get(self):
        cur = copy.copy(self._current)
        self._current = (self._current + self._step) % 0x7F
        return cur

    def data1_set(self, data1):
        self._current = data1
        return cur
        
    data1 = property(data1_get, data1_set)
