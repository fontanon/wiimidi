import ply.lex as lex
import ply.yacc as yacc
import os

import conf

class Parser():
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.debug = kw.get('debug', 0)
        self.names = { }
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[1] + "_" \
            + self.__class__.__name__
        except:
            modname = "parser"+"_"+self.__class__.__name__
        self.debugfile = modname + ".dbg"
        self.tabmodule = modname + "_" + "parsetab"

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile,
                  write_tables=0) #FIXME: Smarter parsetab managing it's needed
                  #tabmodule="parsetab.py")

    def run(self):
        while 1:
            try:
                s = raw_input('parser > ')
            except EOFError:
                break
            if not s: continue
            yacc.parse(s)

    def load(self, path):
        self.names = {}
        f = open(path, 'r')
        yacc.parse(f.read())
        f.close()
        
class WidParser(Parser):
    literals = '.,=()+'
    tokens = (
        'COMMENT', 'NUMBER',
        'WIIMOTE', 'WIIBUTTON', 'NUNCHUK', 'NUNBUTTON', 'BTNEVENT',
        'NOTE',
        )

    t_WIIMOTE = r'Wiimote'
    t_WIIBUTTON = r'A|B|Left|Right|Up|Down|Minus|Plus|Home|1|2'
    t_NUNCHUK = r'Nunchuk'
    t_NUNBUTTON = r'C|Z'
    t_BTNEVENT = r'Press|Release'
    t_NOTE = r'NOTE'
    t_ignore  = ' \t'
        
    def __init__(self):
        Parser.__init__(self)
        self.conf = conf.Conf()
        
    def t_COMMENT(self, t):
        r'\#.*'
        pass
        
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)    
        return t
        
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    def p_program(self, p):
        """ program : program expression
                    | expression """

        p[0] = None

    def p_expression(self, p):
        """ expression : buttonassign """
        # | axisassign """
        p[0] = p[1]
                       
    def p_buttonassign(self, p):
        """ buttonassign : button '=' midicmd
                         | button '.' BTNEVENT '=' midicmd """

        if len(p) == 4:
            p[1].set_press_action(p[3])
            if p[3].reversible:
                p[1].set_release_action(-p[3])
        else:
            if p[3] == 'Press':
                p[1].set_press_action(p[5])
            else:
                p[1].set_release_action(p[5])

        self.conf.add_btn(p[1])
        p[0] = p[1]
        
    def p_button(self, p):
        """ button : WIIMOTE '.' WIIBUTTON
                   | NUNCHUK '.' NUNBUTTON """

        if p[1] == 'Wiimote':
            button = conf.WiimoteButton(''.join(p[1:]))
            if button in self.conf.wiimote_bmap.values():
                button = self.conf.wiimote_bmap[button.code]
        elif p[1] == 'Nunchuk':
            button = conf.NunchukButton(''.join(p[1:]))
            if button in self.conf.nunchuk_bmap.values():
                button = self.conf.nunchuk_bmap[button.code]
                 
        p[0] = button
            
    def p_midicmd(self, p):
        """ midicmd : NOTE '(' NUMBER ',' NUMBER ')' 
                    | NOTE '(' NUMBER ',' NUMBER ',' NUMBER ')' """
        
        if len(p) == 7:
            p[0] = conf.Note(p[3], p[5])
        else:
            p[0] = conf.Note(p[3], p[5], p[7])
        
    def p_error(self, p):
        if p:
            print "Syntax error at '%s'" % p.value
        else:
            print "Syntax error at EOF"
