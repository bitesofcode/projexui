""" Defines the XZoomSlider class """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QWidget,\
                              QSlider,\
                              QToolButton,\
                              QHBoxLayout,\
                              QIcon

import projexui.resources

class XZoomSlider(QWidget):
    zoomAmountChanged   = Signal(int)
    
    def __init__(self, parent=None):
        super(XZoomSlider, self).__init__(parent)
        
        # define the interface
        in_icon  = projexui.resources.find('img/zoom_in.png')
        out_icon = projexui.resources.find('img/zoom_out.png')
        
        self._zoomInButton = QToolButton(self)
        self._zoomInButton.setAutoRaise(True)
        self._zoomInButton.setToolTip('Zoom In')
        self._zoomInButton.setIcon(QIcon(in_icon))
        
        self._zoomOutButton = QToolButton(self)
        self._zoomOutButton.setAutoRaise(True)
        self._zoomOutButton.setToolTip('Zoom Out')
        self._zoomOutButton.setIcon(QIcon(out_icon))
        
        self._zoomSlider = QSlider(Qt.Horizontal, self)
        self._zoomSlider.setRange(10, 100)
        self._zoomSlider.setValue(100)
        
        # define the layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._zoomOutButton)
        layout.addWidget(self._zoomSlider)
        layout.addWidget(self._zoomInButton)
        
        self.setLayout(layout)
        
        # create connections
        self._zoomSlider.valueChanged.connect(self.emitZoomAmountChanged)
        self._zoomInButton.clicked.connect(self.zoomIn)
        self._zoomOutButton.clicked.connect(self.zoomOut)
    
    def emitZoomAmountChanged(self):
        """
        Emits the current zoom amount, provided the signals are not being
        blocked.
        """
        if not self.signalsBlocked():
            self.zoomAmountChanged.emit(self.zoomAmount())
    
    def maximum(self):
        """
        Returns the maximum zoom level for this widget.
        
        :return     <int>
        """
        return self._zoomSlider.maximum()
    
    def minimum(self):
        """
        Returns the minimum zoom level for this widget.
        
        :return     <int>
        """
        return self._zoomSlider.minimum()
    
    @Slot(int)
    def setMaximum(self, maximum):
        """
        Sets the maximum zoom level for this widget.
        
        :param      maximum | <int>
        """
        self._zoomSlider.setMaximum(maximum)
    
    @Slot(int)
    def setMinimum(self, minimum):
        """
        Sets the minimum zoom level for this widget.
        
        :param      minimum | <int>
        """
        self._zoomSlider.setMinimum(minimum)
    
    def setZoomStep(self, amount):
        """
        Sets how much a single step for the zoom in/out will be.
        
        :param      amount | <int>
        """
        self._zoomSlider.setPageStep(amount)
    
    @Slot(int)
    def setZoomAmount(self, amount):
        """
        Sets the zoom amount for this widget to the inputed amount.
        
        :param      amount | <int>
        """
        self._zoomSlider.setValue(amount)
    
    def zoomAmount(self):
        """
        Returns the current zoom amount for this widget.
        
        :return     <int>
        """
        return self._zoomSlider.value()
    
    @Slot()
    def zoomIn(self):
        """
        Zooms in by a single page step.
        """
        self._zoomSlider.triggerAction(QSlider.SliderPageStepAdd)
    
    def zoomInButton(self):
        """
        Returns the zoom in button from the left side of this widget.
        
        :return     <QToolButton>
        """
        return self._zoomInButton
    
    @Slot()
    def zoomOut(self):
        """
        Zooms out by a single page step.
        """
        self._zoomSlider.triggerAction(QSlider.SliderPageStepSub)
    
    def zoomOutButton(self):
        """
        Returns the zoom out button from the right side of this widget.
        
        :return     <QToolButton>
        """
        return self._zoomOutButton
    
    def zoomSlider(self):
        """
        Returns the slider widget of this zoom slider.
        
        :return     <QSlider>
        """
        return self._zoomSlider
    
    def zoomStep(self):
        """
        Returns the amount for a single step when the user clicks the zoom in/
        out amount.
        
        :return     <int>
        """
        return self._zoomSlider.pageStep()
    
    x_maximum  = Property(int, maximum, setMaximum)
    x_minimum  = Property(int, minimum, setMinimum)
    z_zoomStep = Property(int, zoomStep, setZoomStep)

__designer_plugins__ = [XZoomSlider]