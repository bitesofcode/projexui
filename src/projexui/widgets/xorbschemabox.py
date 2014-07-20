""" Defines a combo box for selecting orb schemas """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projexui.qt                import Signal, PyObject
from projexui.widgets.xcombobox import XComboBox

import projex
projex.requires('orb')

try:
    from orb import Orb
except ImportError:
    logger.warning('Orb is required for the XOrbSchemaBox')
    Orb = None

class XOrbSchemaBox(XComboBox):
    """ Defines a combo box that contains schemas from the ORB system. """
    __designer_group__ = 'ProjexUI - ORB'
    
    currentSchemaChanged = Signal(PyObject)
    currentTableChanged  = Signal(PyObject)
    
    def __init__( self, parent = None ):
        super(XOrbSchemaBox, self).__init__( parent )
        
        # define custom properties
        self._schemas       = []
        
        if ( Orb ):
            self.setSchemas(Orb.instance().schemas())
        
        # create connections
        self.currentIndexChanged.connect( self.emitCurrentChanged )
    
    def currentSchema( self ):
        """
        Returns the schema found at the current index for this combo box.
        
        :return        <orb.TableSchema> || None
        """
        index = self.currentIndex()
        if ( 0 <= index and index < len(self._schemas) ):
            return self._schemas[index]
        return None
    
    def emitCurrentChanged( self ):
        """
        Emits the current schema changed signal for this combobox, provided \
        the signals aren't blocked.
        """
        if ( not self.signalsBlocked() ):
            schema = self.currentSchema()
            self.currentSchemaChanged.emit(schema)
            if ( schema ):
                self.currentTableChanged.emit(schema.model())
            else:
                self.currentTableChanged.emit(None)
    
    def iconMapper( self ):
        """
        Returns the icon mapping method to be used for this combobox.
        
        :return     <method> || None
        """
        return self._iconMapper
    
    def labelMapper( self ):
        """
        Returns the label mapping method to be used for this combobox.
        
        :return     <method> || None
        """
        return self._labelMapper
    
    def schemas( self ):
        """
        Returns the schema list that ist linked with this combo box.
        
        :return     [<orb.Table>, ..]
        """
        return self._schemas
    
    def refresh( self ):
        """
        Refreshs the current user interface to match the latest settings.
        """
        schemas         = self.schemas()
        self.blockSignals(True)
        self.clear()
        self.addItems([schema.name() for schema in schemas])
        self.blockSignals(False)
    
    def setCurrentSchema( self, schema ):
        """
        Sets the index for this combobox to the inputed schema instance.
        
        :param      schema      <orb.TableSchema>
        
        :return     <bool> success
        """
        if ( not schema in self._schemas ):
            return False
        
        index = self._schemas.index(schema)
        self.setCurrentIndex(index)
        return True
    
    def setIconMapper( self, mapper ):
        """
        Sets the icon mapping method for this combobox to the inputed mapper. \
        The inputed mapper method should take a orb.Table instance as input \
        and return a QIcon as output.
        
        :param      mapper | <method> || None
        """
        self._iconMapper = mapper
    
    def setLabelMapper( self, mapper ):
        """
        Sets the label mapping method for this combobox to the inputed mapper.\
        The inputed mapper method should take a orb.Table instance as input \
        and return a string as output.
        
        :param      mapper | <method>
        """
        self._labelMapper = mapper
    
    def setSchemas( self, schemas ):
        """
        Sets the schemas on this combobox to the inputed schema list.
        
        :param      schemas | [<orb.Table>, ..]
        """
        self._schemas = schemas
        self.refresh()

__designer_plugins__ = [XOrbSchemaBox]