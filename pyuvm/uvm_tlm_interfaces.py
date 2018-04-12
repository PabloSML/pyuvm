'''
The UVM TLM class hierarchy wraps the behavior of objects (usually Queues) in
a set of classes and objects.

The UVM LRM calls for three levels of classes to implement TLM: ports, exports,
and imp:
(from 12.2.1)

* ports---Instantiated in components that require or use the associate interface
to initiate transaction requests.

* exports---Instantiated by components that forward an implementation of
the methods defined in the associated interface.

* imps---Instantiated by components that provide an implementation of or
directly implement the methods defined.

This is all a bit much for Python which, because of dynamic typing doesn't
need so many layers.

Specifically, pyuvm implements the _imp classes using an abstact base
class and any class that extends the _imp class must provide the associated
functions (becoming an 'export')  There is no longer a need for the
export classes since we don't have to define variables that "forward" the
interface.

Therefore we do not implement 12.2.6
'''

from predefined_component_classes import uvm_component
from queue import Full as QueueFull, Empty as QueueEmpty, Queue
from abc import ABC, abstractmethod
from types import FunctionType
'''
12.2.2
This section describes a variety of classes without
giving each one its own section using * to represent
a variety of implementations (get, put, blocking_put, etc)

Python provides multiple inheritance and we'll use that below
to smooth implementation. Python does not require that we
repeat the __init__ for classes that do not change the 
__init__ functionality.
'''


'''
12.2.7
The _imp classes force users to implement the correct
interface for the various TLM directions. 
'''

class uvm_blocking_put_imp(ABC):
    @abstractmethod
    def put(self,item):
        pass

class uvm_nonblocking_put_imp(ABC):
    @abstractmethod
    def try_put(self,item):
        return None

    @abstractmethod
    def can_put(self):
        return False

class uvm_put_imp(uvm_blocking_put_imp,uvm_nonblocking_put_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_get_imp(ABC):
    @abstractmethod
    def get(self):
        pass

class uvm_nonblocking_get_imp(ABC):
    @abstractmethod
    def try_get(self,item):
        return None

    @abstractmethod
    def can_get(self):
        return False

class uvm_analysis_imp(ABC):
    @abstractmethod
    def write(self, item):
        pass

class uvm_get_imp(uvm_blocking_get_imp,uvm_nonblocking_get_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_peek_imp(ABC):
    @abstractmethod
    def peek(self):
        pass

class uvm_nonblocking_peek_imp(ABC):
    @abstractmethod
    def try_peek(self):
        return None

    @abstractmethod
    def can_peek(self):
        return False

class uvm_peek_imp(uvm_blocking_peek_imp,uvm_nonblocking_peek_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_get_peek_imp(uvm_blocking_get_imp, uvm_blocking_peek_imp):
    '''
    Combine the above
    '''

class uvm_nonblocking_get_peek_imp(uvm_nonblocking_get_imp,uvm_nonblocking_peek_imp):
    '''
    Combining the above
    '''

class uvm_get_peek_imp(uvm_get_imp, uvm_peek_imp):
    '''
    Combing the above
    '''

class uvm_blocking_transport_imp(ABC):
    @abstractmethod
    def transport(self, req):
        '''
        The UVM returns the rsp through the
        parameter list, but we don't do that
        in Python.  So we return either rsp
        or None.
        :param req: Request
        :return: rsp
        '''
        return None

class uvm_non_blocking_transport_imp(ABC):
    @abstractmethod
    def nb_transport(self, req):
        '''
        As above we return None when the UVM version would
        return 0.  Otherwise we return rsp.
        :param req: Request
        :return: rsp as Response
        '''
        return None

class uvm_transport_imp(uvm_blocking_transport_imp, uvm_non_blocking_transport_imp):
    '''
    Must provide both of the above.
    '''

class uvm_blocking_master_imp(uvm_blocking_put_imp, uvm_blocking_get_peek_imp):
    '''
    Everybody blocks
    '''

class uvm_nonblocking_master_imp(uvm_nonblocking_put_imp, uvm_nonblocking_get_peek_imp):
    '''
    Nobody blocks
    '''

class uvm_master_imp(uvm_nonblocking_master_imp, uvm_blocking_master_imp):
    '''
    Block or don't, your choice.
    '''

class uvm_blocking_slave_imp(uvm_blocking_put_imp, uvm_blocking_get_peek_imp):
    '''
    Everybody blocks
    '''

class uvm_nonblocking_slave_imp(uvm_nonblocking_put_imp, uvm_nonblocking_get_peek_imp):
    '''
    Nobody blocks
    '''

class uvm_slave_imp(uvm_nonblocking_slave_imp, uvm_blocking_slave_imp):
    '''
    Block or don't, your choice.
    '''


'''
12.2.5
Port Classes

The following port classes can be connected to "export" classes.
They check that the export is of the correct type.

uvm_port_base adds the correct methods to this class
rather than reference them because Python allows 
you to assign functions to objects dynamically.
'''

class uvm_port_base(uvm_component):
    '''
    port classes expose the tlm methods to
    the object that instantiates them.  We extend
    this class to create the variety of ports and
    pass this class the implementation type that
    defines the needed methods (put(), get(),
    nb_transport(), etc)

    Connect dynamically adds the functions'
    concrete implementations to the port and
    wraps them so that port.put() calls export.put()



    '''

    def __init__(self, name, parent, imp_type):
        super().__init__(name, parent)
        self.connected_to={}
        self._imp_type=imp_type
        self.uvm_methods = [uvm_method
                            for uvm_method in dir ( imp_type )
                            if isinstance( getattr( imp_type, uvm_method ), FunctionType )]

    def connect(self, export):
        '''
        connect() takes an object that implements _imp_type
        and wraps its implementing methods in the port. That
        way any port can deliver the methods of any imp
        :param export: The concrete object that implements imp
        :return: None
        '''
        isinstance( export, self._imp_type )
        self.__export=export
        self.connected_to[export.full_name]=export
        export.provided_to[self.full_name]=self
        for method in self.uvm_methods:
            exec( f'self.{method}=self.__export.{method}' )

class uvm_blocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_put_imp)

class uvm_nonblocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_put_imp)

class uvm_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_put_imp)

class uvm_blocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_imp)

class uvm_nonblocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_imp)

class uvm_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_imp)

class uvm_blocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_peek_imp)

class uvm_nonblocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_peek_imp)

class uvm_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_peek_imp)

class uvm_blocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_peek_imp)

class uvm_nonblocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_peek_imp)

class uvm_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_peek_imp)

class uvm_analyis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_analysis_imp)


'''
12.2.8 FIFO Classes

These classes provide synchronization control between
threads using the Queue class.

'''

class uvm_tlm_fifo_base(uvm_component):

    class PutExport(uvm_put_imp):
        '''
        12.2.8.1.3
        '''
        def put(self,item):
            self.__queue.put(item)

        def can_put(self):
            return not self.__queue.full()

        def try_put(self, item):
            try:
                self.__queue.put_nowait ( item )
                return True
            except QueueFull:
                return False

    class GetPeekExport(uvm_get_peek_imp):
        '''
        12.2.8.1.4
        '''
        def get(self):
            return self.__queue.get()

        def can_get(self):
            return not self.__queue.empty()

        def try_get(self):
            try:
                return self.__queue.get_nowait ()
            except QueueEmpty:
                return None
        def peek(self):
            while self.__queue.empty ():
                self.__queue.not_empty.wait ()
            queue_data = self.__queue.queue
            return queue_data[0]

    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.__queue=None
        self.put_export=PutExport()



'''
UVM TLM 2
12.3

This is left for future development.
'''
