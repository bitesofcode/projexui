#!/usr/bin/python

""" Defines a chart widget for use in displaying data. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2013, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt import wrapVariant
from projexui.qt.QtCore import QMimeData
from projexui.qt.QtGui import QGraphicsPathItem, QDrag

class XChartDatasetItem(QGraphicsPathItem):
    def __init__(self, *args):
        super(XChartDatasetItem, self).__init__(*args)
        
        # define custom properties
        self._dataset = None
        self._buildData = {}
        
        self.setAcceptHoverEvents(True)
    
    def axis(self, name):
        """
        Returns the axis for this item.
        
        :param      name | <str>
        """
        try:
            return self.scene().chart().axis(name)
        except AttributeError:
            return None
    
    def buildData(self, key=None, default=None):
        """
        Returns the build information for this item for the given key, 
        or all build information if the supplied key is None.
        
        :param      key     | <str> || None
                    default | <variant>
        
        :return     <variant>
        """
        if key is None:
            return self._buildData
        
        return self._buildData.get(nativestring(key), default)
    
    def dataset(self):
        """
        Returns the dataset instance associated with this item.
        
        :return     <XChartDataset>
        """
        return self._dataset
    
    def mousePressEvent(self, event):
        """
        Creates the drag event for this item.
        
        :param      event | <QMousePressEvent>
        """
        ddata = self.dataset().dragData()
        if ddata:
            self.startDrag(ddata)
        
        super(XChartDatasetItem, self).mousePressEvent(event)
    
    def paint(self, painter, option, widget):
        """
        Draws this item with the inputed painter.  This will call the
        scene's renderer to draw this item.
        """
        scene = self.scene()
        if not scene:
            return
        
        scene.chart().renderer().drawItem(self, painter, option)
    
    def setBuildData(self, key, value):
        """
        Returns the build information for this item for the given key, 
        or all build information if the supplied key is None.
        
        :param      key   | <str>
                    value | <variant>
        """
        self._buildData[nativestring(key)] = value
    
    def setDataset(self, dataset):
        """
        Sets the dataset instance associated with this item.
        
        :param      dataset | <XChartDataset>
        """
        self._dataset = dataset
        
        # setup the tooltip
        tip = []
        tip.append('<b>%s</b>' % dataset.name())
        for value in dataset.values():
            value_text = []
            for key, val in sorted(value.items()):
                if val == dataset.name():
                    continue
                
                axis = self.axis(key)
                if axis and axis.labelFormat():
                    val = axis.labelFormat().format(val)
                value_text.append('%s: %s' % (key, val))
            
            tip.append('<p>%s</p>' % ', '.join(value_text))
        self.setToolTip(''.join(tip))
    
    def startDrag(self, dragData):
        """
        Starts a new drag with the inputed data.
        
        :param      dragData | <dict>
        """
        # create the mime data
        mimeData = QMimeData()
        for key, value in dragData.items():
            mimeData.setData('application/x-%s' % key, wrapVariant(value))
        
        # create the drag instance
        drag = QDrag(self.scene().chart())
        drag.setMimeData(mimeData)
        drag.exec_()
        