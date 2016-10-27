""" Defines logging record widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

#------------------------------------------------------------------------------

import datetime
import logging
import threading
import projexui

from projexui import resources
from projexui.widgets.xtreewidget import XTreeWidgetItem
from xml.etree import ElementTree
from xqt import wrapVariant, unwrapVariant, QtGui, QtCore

from .xlogrecordcontrols import XLogRecordControls
from .xlogrecordhandler import XLogRecordHandler

class XLogRecordItem(XTreeWidgetItem):
    Colors = {
        logging.DEBUG:      'gray',
        logging.INFO:       'blue',
        logging.SUCCESS:    'darkGreen',
        logging.WARNING:    'brown',
        logging.ERROR:      'darkRed',
        logging.CRITICAL:   'darkRed'
    }
    def __init__(self, parent, record):
        super(XLogRecordItem, self).__init__(parent)
        
        # set default properties
        self.setFixedHeight(22)
        
        created = datetime.datetime.fromtimestamp(record.created)
        
        self.setData( 0, QtCore.Qt.DisplayRole, wrapVariant(record.levelname))
        self.setData( 1, QtCore.Qt.DisplayRole, wrapVariant(record.levelno))
        self.setData( 2, QtCore.Qt.DisplayRole, wrapVariant(record.name))
        self.setData( 3, QtCore.Qt.DisplayRole, wrapVariant(str(created)))
        self.setData( 4, QtCore.Qt.DisplayRole, wrapVariant(record.message))
        self.setData( 5, QtCore.Qt.DisplayRole, wrapVariant('% 10.4f' % (record.relativeCreated / 1000.0)))
        self.setData( 6, QtCore.Qt.DisplayRole, wrapVariant(record.filename))
        self.setData( 7, QtCore.Qt.DisplayRole, wrapVariant(record.module))
        self.setData( 8, QtCore.Qt.DisplayRole, wrapVariant(record.funcName))
        self.setData( 9, QtCore.Qt.DisplayRole, wrapVariant(record.lineno))
        self.setData(10, QtCore.Qt.DisplayRole, wrapVariant(record.pathname))
        self.setData(11, QtCore.Qt.DisplayRole, wrapVariant(record.process))
        self.setData(12, QtCore.Qt.DisplayRole, wrapVariant(record.processName))
        self.setData(13, QtCore.Qt.DisplayRole, wrapVariant(record.thread))
        self.setData(14, QtCore.Qt.DisplayRole, wrapVariant(record.threadName))
        
        clr = XLogRecordItem.Colors.get(record.levelno)
        if clr:
            for i in range(self.columnCount()):
                self.setForeground(i, QtGui.QColor(clr))
        
        # create custom properties
        self._record = record

    def record(self):
        """
        Returns the record for this instance.
        
        :return     <logging.LoggerRecord>
        """
        return self._record

#----------------------------------------------------------------------

class XLogRecordWidget(QtGui.QWidget):
    """ """
    def __init__( self, parent = None ):
        super(XLogRecordWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._handler = XLogRecordHandler(self)
        self._destroyed = False
        self._loggers = set()
        self._activeLevels = []
        self._queue = []
        self._timer = QtCore.QTimer()
        self._timer.setInterval(500)  # only load records every 500 msecs
        
        # update the feedback
        id = threading.currentThread().ident
        self.uiFeedbackLBL.setText('Main thread: {0}'.format(id))
        
        # update the interface
        font = QtGui.QFont('Courier New')
        font.setPointSize(9)
        self.uiRecordTREE.setFont(font)
        self.uiRecordTREE.setVisibleColumns(['Level', 'Name', 'Message'])
        self.uiRecordTREE.setFilteredColumns(list(range(self.uiRecordTREE.columnCount())))
        self.updateUi()
        
        # setup the configurations
        popup = self.uiSettingsBTN.popupWidget()
        popup.setShowTitleBar(False)
        popup.setResizable(False)
        
        bbox = popup.buttonBox()
        bbox.clear()
        bbox.addButton(QtGui.QDialogButtonBox.Ok)
        
        # create the logger tree widget
        controls = XLogRecordControls(self)
        self.uiSettingsBTN.setCentralWidget(controls)
        self.uiSettingsBTN.setDefaultAnchor(popup.Anchor.TopRight)
        
        self._timer.start()
        
        # create connections
        self._timer.timeout.connect(self.loadQueue)
        self._handler.dispatch().recordLogged.connect(self.addRecord)
        
        self.uiRecordBTN.toggled.connect(self.updateUi)
        self.uiRecordTREE.customContextMenuRequested.connect(self.showMenu)
        self.destroyed.connect(self.markDestroyed)

    def activeLevels(self):
        """
        Returns the active levels that will be displayed for this widget.
        
        :return     [<int>, ..]
        """
        return self._activeLevels
    
    def addLogger(self, logger, level=logging.INFO):
        """
        Adds the inputed logger to the list of loggers that are being tracked
        with this widget.
        
        :param      logger | <logging.Logger> || <str>
                    level  | <logging.LEVEL>
        """
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if logger in self._loggers:
            return
        
        # allow the handler to determine the level for this logger
        if logger == 'root':
            _log = logging.getLogger()
        else:
            _log = logging.getLogger(logger)
        
        _log.addHandler(self.handler())
        
        self._loggers.add(logger)
        self.handler().setLoggerLevel(logger, level)
    
    def addRecord(self, record):
        """
        Adds the inputed record to this logger tree widget.
        
        :param      record | <logging.LogRecord>
        """
        if self._destroyed:
            return
        
        if not self.uiRecordBTN.isChecked():
            return
        
        self._queue.append(record)

    def cleanup(self):
        self._destroyed = True
        
        try:
            self._handler.dispatch().recordLogged.disconnect(self.addRecord)
        except StandardError:
            pass
        
        try:
            self._timer.stop()
        except StandardError:
            pass

    def clear(self):
        """
        Clears the information for this widget.
        """
        self.uiRecordTREE.clear()

    def clearLoggers(self, logger):
        """
        Removes the inputed logger from the set for this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        for logger in self._loggers:
            if logger == 'root':
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(logger)
            logger.removeHandler(self.handler())
        
        self._loggers = set()
    
    def handler(self):
        """
        Returns the logging handler that is linked to this widget.
        
        :return     <XLoggerWidgetHandler>
        """
        return self._handler
    
    def hasLogger(self, logger):
        """
        Returns whether or not the inputed logger is tracked by this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        if isinstance(logger, logging.Logger):
            logger = logging.name
        
        return logger in self._loggers
    
    def loadQueue(self):
        if not self._queue:
            return
        
        tree = self.uiRecordTREE
        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        lvls = self.activeLevels()
        records = list(self._queue)
        self._queue = []
        for record in records:
            item = XLogRecordItem(tree, record)
            if lvls and record.levelno not in lvls:
                item.setHidden(True)
        tree.setUpdatesEnabled(True)
        tree.blockSignals(False)
        tree.scrollToBottom()
    
    def loggerLevels(self):
        """
        Returns a dictionary of the set logger levels for this widget.
        
        :return     {<str> logger: <int> level, ..}
        """
        return self._handler.loggerLevels()
    
    def markDestroyed(self):
        self._destroyed = True
    
    def removeLogger(self, logger):
        """
        Removes the inputed logger from the set for this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if logger in self._loggers:
            self._loggers.remove(logger)
            if logger == 'root':
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(logger)
            
            logger.removeHandler(self.handler())
    
    def restoreSettings(self, settings):
        """
        Restores the settings for this logger from the inputed settings.
        
        :param      <QtCore.QSettings>
        """
        levels = unwrapVariant(settings.value('levels'))
        if levels:
            self.setActiveLevels(map(int, levels.split(',')))
        
        logger_levels = unwrapVariant(settings.value('loggerLevels'))
        if logger_levels:
            for key in logger_levels.split(','):
                logger, lvl = key.split(':')
                lvl = int(lvl)
                self.setLoggerLevel(logger, lvl)
        
        filt = unwrapVariant(settings.value('filter'))
        if filt:
            self.uiFilterTXT.setText(filt)
        self.uiRecordTREE.restoreSettings(settings)

    def restoreXml(self, xml):
        """
        Saves the logging settings for this widget to XML format.
        
        :param      xml | <xml.etree.ElementTree.Element>
        """
        self.uiFilterTXT.setText(xml.get('filter', ''))
        
        xlevels = xml.find('levels')
        xloggerlevels = xml.find('logger_levels')
        xtree = xml.find('tree')
        
        if xlevels is not None and xlevels.text:
            self.setActiveLevels(map(int, xlevels.text.split(',')))
        if xloggerlevels is not None and xloggerlevels.text:
            for key in xloggerlevels.text.split(','):
                logger, lvl = key.split(':')
                lvl = int(lvl)
                self.setLoggerLevel(logger, lvl)
        
        if xtree is not None:
            self.uiRecordTREE.restoreXml(xtree)

    def saveSettings(self, settings):
        """
        Saves the logging settings for this widget to the inputed settings.
        
        :param      <QtCore.QSettings>
        """
        lvls = []
        for logger, level in self.loggerLevels().items():
            lvls.append('{0}:{1}'.format(logger, level))
        
        settings.setValue('filter', wrapVariant(self.uiFilterTXT.text()))
        settings.setValue('levels', wrapVariant(','.join(map(str, self.activeLevels()))))
        settings.setValue('loggerLevels', wrapVariant(','.join(lvls)))
        
        self.uiRecordTREE.saveSettings(settings)
    
    def saveXml(self, xml):
        """
        Saves the logging settings for this widget to XML format.
        
        :param      xml | <xml.etree.ElementTree.Element>
        """
        lvls = []
        for logger, level in self.loggerLevels().items():
            lvls.append('{0}:{1}'.format(logger, level))
        
        xlevels = ElementTree.SubElement(xml, 'levels')
        xlevels.text = ','.join(map(str, self.activeLevels()))
        
        xloggerlevels = ElementTree.SubElement(xml, 'logger_levels')
        xloggerlevels.text = ','.join(lvls)
        
        xml.set('filter', wrapVariant(self.uiFilterTXT.text()))
        
        xtree = ElementTree.SubElement(xml, 'tree')
        self.uiRecordTREE.saveXml(xtree)
    
    def setActiveLevels(self, levels):
        """
        Defines the levels for this widgets visible/processed levels.
        
        :param      levels | [<int>, ..]
        """
        self._activeLevels = levels
        tree = self.uiRecordTREE
        tree.setUpdatesEnabled(False)
        tree.blockSignals(True)
        
        for i in tree.topLevelItems():
            if levels and i.record().levelno not in levels:
                i.setHidden(True)
            else:
                i.setHidden(False)
        
        tree.blockSignals(False)
        tree.setUpdatesEnabled(True)
    
    def setLoggerLevel(self, logger, level):
        """
        Returns the logging level for the inputed logger.
        
        :param      logger | <logging.Logger> || <str>
                    level  | <logging.LEVEL>
        """
        if level == logging.NOTSET:
            self.removeLogger(logger)
            self.handler().setLoggerLevel(logger, level)
            return
            
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if not logger in self._loggers:
            self.addLogger(logger, level)
        else:
            self.handler().setLoggerLevel(logger, level)

    def showMenu(self, point):
        menu = QtGui.QMenu(self)
        acts = {}
        acts['clear'] = menu.addAction('Clear logs')
        menu.addSeparator()
        
        acts['copy'] = menu.addAction('Copy')
        acts['cut'] = menu.addAction('Cut')
        acts['paste'] = menu.addAction('Paste')
        
        trigger = menu.exec_(QtGui.QCursor.pos())
        if trigger == acts.get('clear'):
            self.clear()

    def updateUi(self):
        if self.uiRecordBTN.isChecked():
            ico = resources.find('img/debug/break.png')
            clr = QtGui.QColor('red')
            self.uiRecordBTN.blink(True)
        else:
            ico = resources.find('img/debug/continue.png')
            clr = QtGui.QColor('blue')
            self.uiRecordBTN.blink(False)
        
        self.uiRecordBTN.setIcon(QtGui.QIcon(ico))
        palette = self.uiRecordBTN.palette()
        palette.setColor(palette.Shadow, clr)
        self.uiRecordBTN.setPalette(palette)

