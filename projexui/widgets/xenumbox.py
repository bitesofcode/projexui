""" Defines a widget for editing enumerated types """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt import Signal, Property
from projexui.widgets.xcombobox import XComboBox

class XEnumBox(XComboBox):
    """ 
    Creates a widget for editing enumerated types easily.  By default, 
    this will be a single selection widget, but if you want a bit or operation 
    for the value, set the checkable state to True.
    
    This class inherits the [[./xcombobox-XComboBox|XComboBox]] class and 
    utilizes the enum class from the [[$API/projex/enum-enum|projex.enum]] module.
    
    == Example ==
    
    |>>> from projexui.widgets.xenumbox import XEnumBox
    |>>> import projexui
    |
    |>>> # create the enum box
    |>>> combo = projexui.testWidget(XEnumBox)
    |
    |>>> # create the enum type
    |>>> from projex.enum import enum
    |>>> Type = enum('Normal', 'Rounded', 'Smooth')
    |
    |>>> # link the enum to the combo
    |>>> combo.setEnum(Type)
    |
    |>>> # set the enum value
    |>>> combo.setCurrentValue(Type.Smooth)
    |
    |>>> # set the combobox enum values
    |>>> combo.setCheckable(True)
    |
    |>>> # set multiple values at once
    |>>> combo.setCurrentValue(Type.Smooth | Type.Rounded)
    |
    |>>> # retrieve the current value
    |>>> combo.currentValue()
    |4
    |
    |>>> # connect to signals
    |>>> def printValue(value): print value
    |>>> combo.valueChanged.connect(printValue)
    
    """
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super(XEnumBox, self).__init__( parent )
        
        # define custom properties
        self._enum = None
        self._required = False
        self._sortByKey = True
        
        # set default properties
        
        # create connections
        self.currentIndexChanged.connect( self.emitValueChanged )
        self.checkedIndexesChanged.connect( self.emitValueChanged )
    
    def currentValue(self):
        """
        Returns the current value for the widget.  If this widget is checkable
        then the bitor value for all checked items is returned, otherwise, the
        selected value is returned.
        
        :return     <int>
        """
        enum  = self.enum()
        if ( self.isCheckable() ):
            value = 0
            for i in self.checkedIndexes():
                value |= enum[nativestring(self.itemText(i))]
            return value
        else:
            try:
                return enum[nativestring(self.itemText(self.currentIndex()))]
            except KeyError:
                return 0
    
    def enum(self):
        """
        Returns the enum type that is linked with this widget.
        
        :return     <projex.enum.enum>
        """
        return self._enum
    
    def emitValueChanged(self):
        """
        Emits the value changed signal with the current value if the signals
        for this widget aren't currently being blocked.
        """
        if not self.signalsBlocked():
            self.valueChanged.emit(self.currentValue())
    
    def isRequired(self):
        """
        Returns whether or not a value is required for this enumeration.
        
        :return     <bool>
        """
        return self._required
    
    def reload(self):
        """
        Reloads the contents for this box.
        """
        enum = self._enum
        if not enum:
            return
        
        self.clear()
        
        if not self.isRequired():
            self.addItem('')
        
        if self.sortByKey():
            self.addItems(sorted(enum.keys()))
        else:
            items = enum.items()
            items.sort(key = lambda x: x[1])
            
            self.addItems(map(lambda x: x[0], items))
    
    def setEnum(self, enum):
        """
        Sets the enum to the inputed enumerated value.
        
        :param      enum | <projex.enum.enum>
        """
        self._enum = enum
        self.reload()
    
    def setRequired(self, state):
        """
        Sets whether or not the value is required for this enumeration.
        
        :param      state | <bool>
        """
        self._required = state
    
    def setCurrentValue(self, value):
        """
        Sets the value for the combobox to the inputed value.  If the combobox 
        is in a checkable state, then the values will be checked, otherwise,
        the value will be selected.
        
        :param      value | <int>
        """
        enum = self.enum()
        if not enum:
            return
        
        if self.isCheckable():
            indexes = []
            for i in range(self.count()):
                try:
                    check_value = enum[nativestring(self.itemText(i))]
                except KeyError:
                    continue
                
                if check_value & value:
                    indexes.append(i)
            self.setCheckedIndexes(indexes)
        else:
            try:
                text = enum[value]
            except (AttributeError, KeyError):
                return
            
            self.setCurrentIndex(self.findText(text))
    
    def setSortByKey(self, state):
        """
        Returns whether or not this enum box should sort by key.  If False,
        then the values will be entered based on the value.
        
        :param     state | <bool>
        """
        self._sortByKey = state
    
    def sortByKey(self):
        """
        Returns whether or not this enum box should sort by key.  If False,
        then the values will be entered based on the value.
        
        :return     <bool>
        """
        return self._sortByKey
    
    x_required = Property(bool, isRequired, setRequired)
    x_sortByKey = Property(bool, sortByKey, setSortByKey)
    
__designer_plugins__ = [XEnumBox]