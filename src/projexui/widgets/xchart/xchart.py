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

#------------------------------------------------------------------------------

import projexui
from xml.etree import ElementTree

from projex.text import nativestring

from projexui.qt import Property, wrapVariant, unwrapVariant, Signal
from projexui.qt.QtCore import Qt, QSize, QPoint
from projexui.qt.QtGui import QFrame,\
                              QPalette,\
                              QScrollBar,\
                              QAction,\
                              QIcon,\
                              QApplication

from projexui.widgets.xchart.xchartscene import XChartScene
from projexui.widgets.xchart.xchartaxis import XChartAxis
from projexui.widgets.xchart.xchartrenderer import XChartRenderer
from projexui.xcoloricon import XColorIcon

from projexui import resources

STYLE = """\
QToolBar {
    border: none;
}
QScrollBar:horizontal {
    border: none;
    background: none;
    height: 5px;
    margin: 0px;
}
QScrollBar:vertical {
    border: none;
    background: none;
    width: 5px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    border: 1px solid palette(Mid);
    background: palette(Button);
    min-width: 20px;
}
QScrollBar::handle:vertical {
    border: 1px solid palette(Mid);
    background: palette(Button);
    min-height: 20px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    width: 5px;
    height: 5px;
}"""

TOOLBAR_STYLE="""
QToolButton {
    border: 1px solid palette(Base);
    color: palette(Mid);
}
QToolButton::checked {
    border: 1px solid palette(Mid);
    color: palette(Text);
}
"""

class XChart(QFrame):
    """ """
    middleClicked = Signal(QPoint)
    
    def __init__( self, parent = None ):
        super(XChart, self).__init__( parent )
        
        # load the interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._renderer = None
        self._chartTitle = ''
        self._axes = []
        self._datasets = []
        self._horizontalAxis = None
        self._verticalAxis = None
        self._showDatasetToolbar = True
        self._showTypeButton = True
        self._dataChanged = False
        self._showGrid = True
        self._showRows = True
        self._showColumns = True
        self._showXAxis = True
        self._showYAxis = True
        
        # set default properties
        self.uiChartVIEW.setScene(XChartScene(self))
        self.uiXAxisVIEW.setScene(XChartScene(self))
        self.uiYAxisVIEW.setScene(XChartScene(self))
        self.uiChartVIEW.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.uiXAxisVIEW.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.uiYAxisVIEW.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.uiDatasetTBAR.setFixedHeight(32)
        
        self.uiXAxisVIEW.hide()
        self.uiYAxisVIEW.hide()
        
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Base)
        self.setStyleSheet(STYLE)
        self.uiChartVIEW.setMouseTracking(True)
        self.uiDatasetTBAR.setStyleSheet(TOOLBAR_STYLE)
        
        # load renderers
        for renderer in XChartRenderer.plugins():
            act = QAction('%s Chart' % renderer, self)
            ico = 'img/chart/%s.png' % renderer.lower()
            act.setIcon(QIcon(resources.find(ico)))
            self.uiTypeBTN.addAction(act)
            
            # assign the default renderer
            if not self.uiTypeBTN.defaultAction():
                self._renderer = XChartRenderer.plugin(renderer)
                self.uiTypeBTN.setDefaultAction(act)
        
        # create connections
        chart_hbar = self.uiChartVIEW.horizontalScrollBar()
        chart_vbar = self.uiChartVIEW.verticalScrollBar()
        
        x_bar = self.uiXAxisVIEW.horizontalScrollBar()
        y_bar = self.uiYAxisVIEW.verticalScrollBar()
        
        chart_hbar.valueChanged.connect(self.syncScrollbars)
        chart_hbar.rangeChanged.connect(self.syncScrollbars)
        y_bar.valueChanged.connect(self.syncScrollbars)
        y_bar.rangeChanged.connect(self.syncScrollbars)
        self.uiTypeBTN.triggered.connect(self.assignRenderer)
    
    def _addDatasetAction(self, dataset):
        """
        Adds an action for the inputed dataset to the toolbar
        
        :param      dataset | <XChartDataset>
        """
        # create the toolbar action
        action = QAction(dataset.name(), self)
        action.setIcon(XColorIcon(dataset.color()))
        action.setCheckable(True)
        action.setChecked(True)
        action.setData(wrapVariant(dataset))
        action.toggled.connect(self.toggleDataset)
        
        self.uiDatasetTBAR.addAction(action)
    
    def _drawBackground(self, scene, painter, rect):
        """
        Draws the backgroud for a particular scene within the charts.
        
        :param      scene   | <XChartScene>
                    painter | <QPainter>
                    rect    | <QRectF>
        """
        rect = scene.sceneRect()
        if scene == self.uiChartVIEW.scene():
            self.renderer().drawGrid(painter,
                                     rect,
                                     self.showGrid(),
                                     self.showColumns(),
                                     self.showRows())
        elif scene == self.uiXAxisVIEW.scene():
            self.renderer().drawAxis(painter, rect, self.horizontalAxis())
        elif scene == self.uiYAxisVIEW.scene():
            self.renderer().drawAxis(painter, rect, self.verticalAxis())
    
    def _drawForeground(self, scene, painter, rect):
        """
        Draws the backgroud for a particular scene within the charts.
        
        :param      scene   | <XChartScene>
                    painter | <QPainter>
                    rect    | <QRectF>
        """
        rect = scene.sceneRect()
        if scene == self.uiChartVIEW.scene():
            self.renderer().drawForeground(painter,
                                           rect,
                                           self.showGrid(),
                                           self.showColumns(),
                                           self.showRows())
    
    def addAxis(self, axis):
        """
        Adds a new axis for this chart.  Axis can define X & Y data
        including notch and value processing, as well as define
        individual lines within the chart that any chart items can
        reference or use.
        
        :param      axis | <projexui.widgets.xchart.XChartAxis>
        """
        self._axes.append(axis)
    
    def addDataset(self, dataset):
        """
        Adds the given data set to this chart widget.
        
        :param      dataSet | <XChartDataset>
        """
        self._datasets.append(dataset)
        self._dataChanged = True
        self._addDatasetAction(dataset)
    
    def addToolbarWidget(self, widget):
        """
        Adds a new widget to the toolbar layout for the chart.
        
        :param      widget | <QWidget>
        """
        self.uiToolbarHBOX.addWidget(widget)
    
    def assignRenderer(self, action):
        """
        Assigns the renderer for this chart to the current selected
        renderer.
        """
        name = nativestring(action.text()).split(' ')[0]
        self._renderer = XChartRenderer.plugin(name)
        self.uiTypeBTN.setDefaultAction(action)
        self.recalculate()
    
    def axes(self):
        """
        Returns all the axes that have been defined for this chart.
        
        :return     [<projexui.widgets.xchart.XChartAxis>, ..]
        """
        out = self._axes[:]
        if self._horizontalAxis:
            out.append(self._horizontalAxis)
        if self._verticalAxis:
            out.append(self._verticalAxis)
        return out
    
    def axis(self, name):
        """
        Looks up an axis for this chart by the given name.
        
        :return     <projexui.widgets.xchart.XChartAxis> || None
        """
        for axis in self.axes():
            if axis.name() == name:
                return axis
        return None
    
    def clear(self):
        """
        Clears out all the dataset information from the chart.
        """
        self.clearAxes()
        self.clearDatasets()
    
    def clearAxes(self):
        self._axes = []
        self._verticalAxis = None
        self._horizontalAxis = None
    
    def clearDatasets(self):
        self._datasets = []
        for act in self.uiDatasetTBAR.actions():
            act.deleteLater()
        
        self.uiDatasetTBAR.clear()
        self.uiChartVIEW.scene().clear()
    
    def chartTitle(self):
        """
        Returns the title for this plot.
        
        :return     <str>
        """
        return self._title
    
    def compareValues(self, a, b):
        """
        Compares two values based on their values for this axis.
        
        :param      a | <variant>
                    b | <variant>
        """
        values = self.values()
        try:
            return cmp(values.index(a), values.index(b))
        except ValueError:
            return cmp(a, b)
    
    def datasets(self, visible=True):
        """
        Returns a list of the data sets that are assigned with this
        chart widget.
        
        :param      visible | <bool>
        
        :return     [<XChartDataSet>, ..]
        """
        if visible is not None:
            return filter(lambda x: x.isVisible(), self._datasets)
        return self._datasets[:]
    
    def showEvent(self, event):
        super(XChart, self).showEvent(event)
        self.recalculate()
    
    def findRenderer(self, name):
        """
        Returns the renderer based on the inputed name.
        
        :return     <str>
        """
        return XChartRenderer.plugin(name)
    
    def horizontalAxis(self):
        """
        Returns the axis that is assigned to the horizontal direction for this
        chart.
        
        :return     <XChartAxis>
        """
        return self._horizontalAxis
    
    def insertToolbarWidget(self, index, widget):
        """
        Inserts a new widget to the toolbar layout for the chart.
        
        :param      index  | <int>
                    widget | <QWidget>
        """
        self.uiToolbarHBOX.insertWidget(index, widget)
    
    def pointAt(self, **axis_values):
        """
        Returns the point on the chart where the inputed values are located.
        
        :return     <QPointF>
        """
        scene_point = self.renderer().pointAt(self.axes(), axis_values)
        chart_point = self.uiChartVIEW.mapFromScene(scene_point)
        return self.uiChartVIEW.mapToParent(chart_point)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.middleClicked.emit(event.pos())
        
        super(XChart, self).mousePressEvent(event)
    
    def recalculate(self):
        """
        Recalculates the information for this chart.
        """
        if not (self.isVisible() and self.renderer()):
            return
        
        # update dynamic range
        if self._dataChanged:
            for axis in self.axes():
                if axis.useDynamicRange():
                    axis.calculateRange(self.values(axis.name()))
            
            self._dataChanged = False
        
        # recalculate the main grid
        xaxis = self.horizontalAxis()
        yaxis = self.verticalAxis()
        renderer = self.renderer()
        
        xvisible = xaxis is not None and self.showXAxis() and renderer.showXAxis()
        yvisible = yaxis is not None and self.showYAxis() and renderer.showYAxis()
        
        self.uiXAxisVIEW.setVisible(xvisible)
        self.uiYAxisVIEW.setVisible(yvisible)
        
        # calculate the main view
        view = self.uiChartVIEW
        chart_scene = view.scene()
        chart_scene.setSceneRect(0, 0, view.width() - 2, view.height() - 2)
        rect = renderer.calculate(chart_scene, xaxis, yaxis)
        
        # recalculate the xaxis
        if xaxis and self.showXAxis() and renderer.showXAxis():
            view = self.uiXAxisVIEW
            scene = view.scene()
            scene.setSceneRect(0, 0, rect.width(), view.height())
            scene.invalidate()
        
        # render the yaxis
        if yaxis and self.showYAxis() and renderer.showYAxis():
            view = self.uiYAxisVIEW
            scene = view.scene()
            scene.setSceneRect(0, 0, view.width(), rect.height())
            scene.invalidate()
        
        # recalculate the items
        renderer.calculateDatasets(chart_scene,
                                   self.axes(),
                                   self.datasets())
        
        chart_scene.invalidate()
        
    def removeAxis(self, axis):
        """
        Removes an axis from this chart either by direct reference or by
        name.
        
        :param      axis | <projexui.widgets.XChartAxis> || <str>
        """
        if not isinstance(axis, XChartAxis):
            axis = self.axis(nativestring(axis))
        
        try:
            self._axes.remove(axis)
        except ValueError:
            pass
    
    def renderer(self):
        """
        Returns the current renderer associated with this plot.
        
        :return     <projexui.widgets.xchart.XChartRenderer>
        """
        return self._renderer
    
    def renderers(self):
        """
        Returns the renderer instances associated with this chart.
        
        :return     [<XChartRenderer>, ..]
        """
        return map(XChartRenderer.plugin, XChartRenderer.plugins())
    
    def resizeEvent(self, event):
        """
        Recalculates the chart information when the widget resizes.
        
        :param      event | <QResizeEvent>
        """
        super(XChart, self).resizeEvent(event)
        
        if self.isVisible():
            self.recalculate()
    
    def restoreXml(self, xchart):
        """
        Restores the xml information for this chart.
        
        :param      xparent | <xml.etree.ElementTree.Element>
        """
        if xchart is None:
            return
        
        self.setRenderer(xchart.get('renderer', 'Bar'))
    
    def saveXml(self, xchart):
        """
        Saves the xml information for this chart to the inputed xml.
        
        :param      xchart | <xml.etree.ElementTree.Element>
        """
        if xchart is None:
            return
        
        xchart.set('renderer', self.renderer().name())
    
    def setRenderer(self, renderer):
        """
        Sets the current renderer associated with this plot.
        
        :param      renderer | <XChartRenderer> || <str>
        
        :return     <bool> | success
        """
        if not isinstance(renderer, XChartRenderer):
            renderer = XChartRenderer.plugin(nativestring(renderer))
        
        if renderer is None:
            return False
        
        self._renderer = renderer
        
        for act in self.uiTypeBTN.actions():
            if act.text() == '%s Chart' % renderer.name():
                self.uiTypeBTN.setDefaultAction(act)
                break
        
        return True
    
    def setAxes(self, axes):
        """
        Sets the axes for this chart to the inputed list of axes.
        
        :param      axes | [<projexui.widgets.xchart.XChartAxis>, ..]
        """
        self._axes = axes
    
    def setDatasets(self, datasets):
        """
        Sets the dataset list for this chart to the inputed data.
        
        :param      datasets | [<XChartDataset>, ..]
        """
        self.clearDatasets()
        self._datasets = datasets
        
        for dataset in datasets:
            self._addDatasetAction(dataset)
        
        self._dataChanged = True
        self.recalculate()
    
    def setChartTitle(self, title):
        """
        Sets the title for the plot to the inputed title.
        
        :param      title | <str>
        """
        self._chartTitle = title
    
    def setHorizontalAxis(self, axis):
        """
        Sets the horizontal axis for this chart.
        
        :param      axis | <XChartAxis>
        """
        self._horizontalAxis = axis
        if axis:
            axis.setOrientation(Qt.Horizontal)
            self.uiXAxisVIEW.setFixedHeight(axis.minimumLabelHeight() + 5)
        
        self.uiXAxisVIEW.setVisible(axis is not None)
    
    def setVerticalAxis(self, axis):
        """
        Sets the vertical axis for this chart.
        
        :param      axis | <XChartAxis>
        """
        self._verticalAxis = axis
        if axis:
            axis.setOrientation(Qt.Vertical)
            self.uiYAxisVIEW.setFixedWidth(axis.minimumLabelWidth() + 15)
        
        self.uiYAxisVIEW.setVisible(axis is not None)
    
    def setShowColumns(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showColumns = state
        
    def setShowDatasetToolbar(self, state):
        """
        Sets whether or not the dataset toolbar is visible.
        
        :param      state | <bool>
        """
        self._showDatasetToolbar = state
        if not state:
            self.uiDatasetTBAR.hide()
        else:
            self.uiDatasetTBAR.show()
    
    def setShowGrid(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showGrid = state
    
    def setShowRows(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showRows = state
    
    def setShowTypeButton(self, state):
        """
        Sets whether or not the type button is visible.
        
        :param      state | <bool>
        """
        self._showTypeButton = state
        if not state:
            self.uiTypeBTN.hide()
        else:
            self.uiTypeBTN.show()
    
    def setShowXAxis(self, state):
        """
        Sets the whether or not this renderer should draw the x-axis.
        
        :param      state | <bool>
        """
        self._showXAxis = state
    
    def setShowYAxis(self, state):
        """
        Sets the whether or not this renderer should draw the y-axis.
        
        :param      state | <bool>
        """
        self._showYAxis = state
    
    def showColumns(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showColumns and self.showXAxis()
    
    def showDatasetToolbar(self):
        """
        Returns whether or not the dataset toolbar is visible.
        
        :return     <bool>
        """
        return self._showDatasetToolbar
    
    def showGrid(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showGrid
    
    def showRows(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showRows and self.showYAxis()
    
    def showTypeButton(self):
        """
        Returns whether or not the type button is visible.
        
        :return     <bool>
        """
        return self._showTypeButton
    
    def showXAxis(self):
        """
        Returns whether or not this renderer should draw the x-axis.
        
        :return     <bool>
        """
        return self._showXAxis
    
    def showYAxis(self):
        """
        Returns whether or not this renderer should draw the y-axis.
        
        :return     <bool>
        """
        return self._showYAxis
    
    def sizeHint(self):
        """
        Returns the size hint for this chart.
        """
        return QSize(300, 300)
    
    def syncScrollbars(self):
        """
        Synchronizes the various scrollbars within this chart.
        """
        chart_hbar = self.uiChartVIEW.horizontalScrollBar()
        chart_vbar = self.uiChartVIEW.verticalScrollBar()
        
        x_hbar = self.uiXAxisVIEW.horizontalScrollBar()
        x_vbar = self.uiXAxisVIEW.verticalScrollBar()
        
        y_hbar = self.uiYAxisVIEW.horizontalScrollBar()
        y_vbar = self.uiYAxisVIEW.verticalScrollBar()
        
        x_hbar.setRange(chart_hbar.minimum(), chart_hbar.maximum())
        x_hbar.setValue(chart_hbar.value())
        x_vbar.setValue(0)
        
        chart_vbar.setRange(y_vbar.minimum(), y_vbar.maximum())
        chart_vbar.setValue(y_vbar.value())
        
        y_hbar.setValue(4)
    
    def toggleDataset(self, state, dataset=None):
        """
        Toggles the dataset based on the given action or dataset.
        
        :param      state | <bool>
                    dataset | <XChartDataset>
        """
        if dataset is None and self.sender():
            dataset = unwrapVariant(self.sender().data())
        
        dataset.setVisible(state)
        self._dataChanged = True
        self.recalculate()
    
    def valueAt(self, point):
        """
        Returns the value within the chart for the given point.
        
        :param      point | <QPoint>
        
        :return     {<str> axis name: <variant> value, ..}
        """
        chart_point = self.uiChartVIEW.mapFromParent(point)
        scene_point = self.uiChartVIEW.mapToScene(chart_point)
        return self.renderer().valueAt(self.axes(), scene_point)
    
    def values(self, axis):
        """
        Returns the values of the given axis from all the datasets within
        this chart.
        
        :param      axis | <str>
        
        :return     [<variant>, ..]
        """
        output = []
        for dataset in self.datasets():
            output += dataset.values(axis)
        
        return output
    
    def verticalAxis(self):
        """
        Returns the axis that is used for the vertical view for
        this graph.
        
        :return     <XChartAxis>
        """
        return self._verticalAxis
    
    x_showColumns = Property(bool, showColumns, setShowColumns)
    x_showRows = Property(bool, showRows, setShowRows)
    x_showGrid = Property(bool, showGrid, setShowGrid)
    x_showYAxis = Property(bool, showYAxis, setShowYAxis)
    x_showXAxis = Property(bool, showXAxis, setShowXAxis)
    
    x_showDatasetToolbar = Property(bool,
                                    showDatasetToolbar,
                                    setShowDatasetToolbar)
    
    x_showTypeButton = Property(bool,
                                showTypeButton,
                                setShowTypeButton)