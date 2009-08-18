def logging( f ) :

    def deco( self , *args , **kw ) :

        print "    %s in da house !" % self.name 
        return f( self , *args , **kw )

    return deco


class A( object ) :

    def __init__( self , name ) :
        self.name   = name

    @logging
    def hello( self, caca="shit" ) :
        print '    Yo, %s, %s .... \n' % (caca, self.name)


def test_01() :

    print

    list_names   = [ 'Bert' , 'Cookie Monster' , 
                     'Count Dracula' , 'Ernie' ]

    list_objects = [ A( this_name ) for this_name in list_names ]

    for this_object in list_objects :
        this_object.hello(caca='we')


if __name__ == '__main__' :

    test_01()

