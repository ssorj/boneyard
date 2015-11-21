class Catalog(object):
    '''
    Wrapper class that allows multiple interface classes to be grouped
    together and referenced through a single object.  Details of which
    class provides the implementation of a method can be ignored by the
    caller.  See add_mechanisms comments below.
    '''
    def __init__(self):
        self.mechanisms = []

    def add_mechanisms(self, mechs):
        '''
        Add an item or items to the list of supported mechanisms.
        A mechanism is expected to be an instance of a class containing
        "public" methods that implement some interface.
        When attribute access is done on an instance of Catalog, 
        the mechanism list is searched in order for a class which contains 
        a method of the given name (assuming the attribute is not contained 
        directly in the Catalog instance itself). This allows methods 
        on mechanism objects to be called as if they are attributes of 
        Catalog, without the caller having knowledge of which mechanism
        ultimately provides the method.
        If a mechanism object has an attribute called 'name', a reference to the
        object is added as an attribute of Catalog named 'name'.  This 
        allows a specific mechamism to be used if desired (for example,
        the hold_job method might be invoked as catalog.qmf.hold_job(), ensuring
        that the QMF version is used, rather than catalog.hold_job() which will
        use the first hold_job method located in the mechanism list).
        '''

        # Allow mechanism to be specifially chosen by name
        # rather than determined by precedence order
        # catalog.qmf.Op() vs catalog.Op(), for example
        def make_mech_attr(m):
            if hasattr(m, "name"):
                setattr(self, m.name, m)

        if type(mechs) in (tuple, list):
            for m in mechs:
                self.mechanisms.append(m)
                make_mech_attr(m)
        else:
            self.mechanisms.append(mechs)
            make_mech_attr(mechs)

    def __getattr__(self, name):
        # Reminder, __getattr__ is called when an attribute
        # cannot be found in the object.
        for m in self.mechanisms:
            if hasattr(m, name):
                a = getattr(m, name)
                if callable(a):
                    return a
        raise AttributeError("No mechanism has callable %s" % name)


