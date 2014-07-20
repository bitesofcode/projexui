""" Defines the XLocationWidget widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

# support python 3
try:
    import urllib2 as urllib
    if ( not hasattr(urllib, 'urlencode') ):
        import urllib

except ImportError:
    import urllib

import webbrowser

from projexui.qt import Signal,\
                        Slot,\
                        Property

from projexui.qt.QtGui import QWidget,\
                              QHBoxLayout,\
                              QIcon,\
                              QToolButton

from projex.text import nativestring

from projexui.widgets.xlineedit import XLineEdit
from projexui import resources

class XLocationWidget(QWidget):
    locationChanged = Signal(str)
    locationEdited  = Signal()
    
    def __init__( self, parent ):
        super(XLocationWidget, self).__init__(parent)
        
        # define the interface
        self._locationEdit      = XLineEdit(self)
        self._locationButton    = QToolButton(self)
        self._urlTemplate       = 'http://maps.google.com/maps?%(params)s'
        self._urlQueryKey       = 'q'
        
        self._locationButton.setAutoRaise(True)
        self._locationButton.setIcon(QIcon(resources.find('img/map.png')))
        
        self._locationEdit.setHint('no location set')
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._locationEdit)
        layout.addWidget(self._locationButton)
        
        self.setLayout(layout)
        
        # create connections
        self._locationEdit.textChanged.connect(self.locationChanged)
        self._locationEdit.textEdited.connect(self.locationEdited)
        self._locationButton.clicked.connect(self.browseMaps)
    
    def blockSignals( self, state ):
        """
        Blocks the signals for this widget and its sub-parts.
        
        :param      state | <bool>
        """
        super(XLocationWidget, self).blockSignals(state)
        self._locationEdit.blockSignals(state)
        self._locationButton.blockSignals(state)
    
    def browseMaps( self ):
        """
        Brings up a web browser with the address in a Google map.
        """
        url    = self.urlTemplate()
        params = urllib.urlencode({self.urlQueryKey(): self.location()})
        
        url    = url % {'params': params}
        webbrowser.open(url)
    
    def hint( self ):
        """
        Returns the hint associated with this widget.
        
        :return     <str>
        """
        return self._locationEdit.hint()
    
    def lineEdit( self ):
        """
        Returns the line edit linked with this widget.
        
        :return     <XLineEdit>
        """
        return self._locationEdit
    
    def location( self ):
        """
        Returns the current location from the edit.
        
        :return     <str>
        """
        return nativestring(self._locationEdit.text())
    
    @Slot(str)
    def setHint( self, hint ):
        """
        Sets the hint associated with this widget.
        
        :param      hint | <str>
        """
        self._locationEdit.setHint(hint)
    
    @Slot(str)
    def setLocation( self, location ):
        """
        Sets the location for this widget to the inputed location.
        
        :param      location | <str>
        """
        self._locationEdit.setText(nativestring(location))
    
    def setUrlQueryKey( self, key ):
        """
        Sets the key for the URL to the inputed key.
        
        :param      key | <str>
        """
        self._urlQueryKey = nativestring(key)
    
    def setUrlTemplate( self, templ ):
        """
        Sets the URL path template that will be used when looking up locations
        on the web.
        
        :param      templ | <str>
        """
        self._urlQueryTemplate = nativestring(templ)
    
    def urlQueryKey( self ):
        """
        Returns the query key that will be used for this location.
        
        :return     <str>
        """
        return self._urlQueryKey
    
    def urlTemplate( self ):
        """
        Returns the url template that will be used when mapping this location.
        
        :return     <str>
        """
        return self._urlTemplate
    
    x_hint        = Property(str, hint, setHint)
    x_location    = Property(str, location, setLocation)
    x_urlQueryKey = Property(str, urlQueryKey, setUrlQueryKey)
    x_urlTemplate = Property(str, urlTemplate, setUrlTemplate)

__designer_plugins__ = [XLocationWidget]