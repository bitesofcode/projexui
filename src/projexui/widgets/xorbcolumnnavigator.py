""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt import Signal
from projexui.qt.QtCore import QPoint, Qt
from projexui.qt.QtGui import QIcon
from projexui.widgets.xtreewidget import XTreeWidget, XTreeWidgetItem
from projexui.widgets.xcombobox import XComboBox
from projexui.completers.xjoincompleter import XJoinCompleter

import projexui
from projexui import resources

#----------------------------------------------------------------------

class XOrbColumnItem(XTreeWidgetItem):
    def __init__(self, parent, column):
        super(XOrbColumnItem, self).__init__(parent)
        
        # set custom options
        self._column = column
        self._loaded = False
        
        if column.isReference():
            self.setChildIndicatorPolicy(self.ShowIndicator)
        
        # set default options
        typ = column.columnTypeText(baseOnly=True)
        ico = 'img/orb/coltypes/%s.png' % typ.lower()
        self.setText(0, column.name().strip('_'))
        self.setIcon(0, QIcon(resources.find(ico)))
        self.setFixedHeight(20)
    
    def load(self):
        """
        Loads the children for this item.
        """
        if self._loaded:
            return
        
        self.setChildIndicatorPolicy(self.DontShowIndicatorWhenChildless)
        
        self._loaded = True
        column = self.schemaColumn()
        if not column.isReference():
            return
        
        ref = column.referenceModel()
        if not ref:
            return
        
        columns = sorted(ref.schema().columns(),
                         key=lambda x: x.name().strip('_'))
        for column in columns:
            XOrbColumnItem(self, column)
    
    def schemaColumn(self):
        """
        Returns the column associated with this item.
        
        :return     <orb.Column>
        """
        return self._column

    def setCurrentSchemaColumn(self, column):
        """
        Sets the current item based on the inputed column.
        
        :param      column | <orb.Column> || None
        """
        if column == self._column:
            self.treeWidget().setCurrentItem(self)
            return True
        
        for c in range(self.childCount()):
            if self.child(c).setCurrentSchemaColumn(column):
                self.setExpanded(True)
                return True
        return None

    def setCurrentSchemaPath(self, path):
        """
        Sets the current item based on the inputed column.
        
        :param      path | <str>
        """
        if not path:
            return False
        
        parts = path.split('.')
        name  = parts[0]
        next  = parts[1:]
        
        if name == self.text(0):
            if next:
                self.load()
                path = '.'.join(next)
                for c in range(self.childCount()):
                    if self.child(c).setCurrentSchemaPath(path):
                        self.setExpanded(True)
                        return True
                return False
            else:
                self.treeWidget().setCurrentItem(self)
                return True
        return False
    
#----------------------------------------------------------------------

class XOrbColumnNavigator(XTreeWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    schemaColumnChanged = Signal(object)
    
    def __init__(self, parent=None):
        super(XOrbColumnNavigator, self).__init__( parent )
        
        # define custom properties
        self._tableType = None
        
        # set default properties
        self.setShowGrid(False)
        self.setArrowStyle(True)
        
        # create connections
        self.currentItemChanged.connect(self.emitSchemaColumnChanged)
        self.itemExpanded.connect(self.loadItem)
    
    def currentSchemaColumn(self):
        """
        Returns the current column associated with this navigator.
        
        :return     <orb.Column> || None
        """
        item = self.currentItem()
        if item:
            return item.schemaColumn()
        return None
    
    def currentSchemaPath(self):
        """
        Returns the column path for the current item.  This will be a '.'
        joined path based on the root schema to the given column.
        
        :return     <str>
        """
        item = self.currentItem()
        path = []
        while item:
            path.append(nativestring(item.text(0)))
            item = item.parent()
        
        return '.'.join(reversed(path))
    
    def emitSchemaColumnChanged(self):
        """
        Emits the current column changed signal.
        
        :param      column | <orb.Column> || None
        """
        if not self.signalsBlocked():
            self.schemaColumnChanged.emit(self.currentSchemaColumn())
    
    def loadItem(self, item):
        """
        Loads the item sub-columns.
        """
        item.load()
    
    def refresh(self):
        """
        Resets the data for this navigator.
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        self.clear()
        tableType = self.tableType()
        if not tableType:
            self.setUpdatesEnabled(True)
            self.blockSignals(False)
            return
        
        schema = tableType.schema()
        columns = list(sorted(schema.columns(),
                              key=lambda x: x.name().strip('_')))
        for column in columns:
            XOrbColumnItem(self, column)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def setCurrentSchemaColumn(self, column):
        """
        Sets the current column associated with this navigator.
        
        :param     column | <orb.Column>
        """
        if not column:
            self.setCurrentItem(None)
            return
        
        for item in self.topLevelItems():
            if item.setCurrentSchemaColumn(column):
                return
        
        self.setCurrentItem(None)
    
    def setCurrentSchemaPath(self, path):
        """
        Sets the column path for the current item.  This will be a '.'
        joined path based on the root schema to the given column.
        
        :param      path | <str>
        """
        if not path:
            self.setCurrentItem(None)
            return False
        
        for item in self.topLevelItems():
            if item.setCurrentSchemaPath(nativestring(path)):
                return True
        
        self.setCurrentItem(None)
        return False
        
    def setTableType(self, tableType):
        """
        Sets the table type for this instance to the inputed table type.
        
        :param      tableType | <subclass of orb.TableType>
        """
        self._tableType = tableType
        self.refresh()
    
    def tableType(self):
        """
        Returns the table type for this instance.
        
        :return     <subclass of orb.TableType> || None
        """
        return self._tableType

#----------------------------------------------------------------------

class XOrbColumnNavigatorBox(XComboBox):
    __designer_group__ = 'ProjexUI - ORB'
    
    schemaColumnChanged = Signal(object)
    
    def __init__(self, parent):
        self._navigator = None
        
        super(XOrbColumnNavigatorBox, self).__init__(parent)
    
    def acceptColumn(self):
        """
        Accepts the current item as the current column.
        """
        self.navigator().hide()
        self.lineEdit().setText(self.navigator().currentSchemaPath())
        self.emitSchemaColumnChanged(self.navigator().currentColumn())
    
    def clearNavigator(self):
        if self._navigator is not None:
            self._navigator.deleteLater()
            self._navigator = None
    
    def currentSchemaColumn(self):
        """
        Returns the current column associated with this box.
        
        :return     <orb.Column> || None
        """
        return self.navigator().currentSchemaColumn()
    
    def currentSchemaPath(self):
        return self.navigator().currentSchemaPath()
    
    def deleteLater(self):
        self.clearNavigator()
        super(XOrbColumnNavigator, self).deleteLater()
    
    def emitSchemaColumnChanged(self, column):
        """
        Emits the current column changed signal.
        
        :param      column | <orb.Column> || None
        """
        edit = self.lineEdit()
        if edit:
            edit.setText(self.navigator().currentSchemaPath())
            
        if not self.signalsBlocked():
            self.schemaColumnChanged.emit(column)
    
    def eventFilter(self, object, event):
        """
        Filters events for the popup tree widget.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :retuen     <bool> | consumed
        """
        try:
            is_lineedit = object == self.lineEdit()
        except RuntimeError:
            is_lineedit = False
        
        try:
            is_nav = object == self._navigator
        except RuntimeError:
            is_nav = False
        
        if not (is_nav or is_lineedit):
            return super(XOrbColumnNavigatorBox, self).eventFilter(object, event)
        
        if event.type() == event.KeyPress:
            # accept lookup
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                self.acceptColumn()
                event.accept()
                return True
                
            # cancel lookup
            elif event.key() == Qt.Key_Escape:
                self.hidePopup()
                event.accept()
                return True
            
            # update the search info
            else:
                self.lineEdit().keyPressEvent(event)
                event.accept()
                return True
        
        elif is_nav and event.type() == event.Show:
            object.resizeToContents()
            object.horizontalScrollBar().setValue(0)
            
        elif event.type() == event.KeyRelease:
            self.lineEdit().keyReleaseEvent(event)
            self.navigator().blockSignals(True)
            self.navigator().setCurrentSchemaPath(self.lineEdit().text())
            self.navigator().blockSignals(False)
            event.accept()
            return True
        
        elif event.type() == event.MouseButtonPress:
            local_pos = object.mapFromGlobal(event.globalPos())
            in_widget = object.rect().contains(local_pos)
            
            if not in_widget:
                self.hidePopup()
                event.accept()
                return True
            
        return super(XOrbColumnNavigatorBox, self).eventFilter(object, event)
    
    def hidePopup(self):
        """
        Overloads the hide popup method to handle when the user hides
        the popup widget.
        """
        self.navigator().hide()
    
    def navigator(self):
        """
        Returns the navigator associated with this box.
        
        :return     <XOrbColumnNavigator>
        """
        if self._navigator is None:
            self._navigator = nav = XOrbColumnNavigator()
            self.lineEdit().setCompleter(None)
            
            # initialize settings
            nav.hide()
            nav.header().hide()
            nav.setWindowFlags(Qt.Popup)
            nav.setFocusPolicy(Qt.ClickFocus)
            nav.installEventFilter(self)
            nav.setVerticalScrollMode(nav.ScrollPerPixel)
            
            # create connections
            nav.itemClicked.connect(self.acceptColumn)
            self.lineEdit().textEdited.connect(self.showPopup)
            nav.schemaColumnChanged.connect(self.emitSchemaColumnChanged)
        
        return self._navigator
    
    def setCurrentSchemaColumn(self, column):
        return self.navigator().setCurrentSchemaColumn(column)
    
    def setCurrentSchemaPath(self, path):
        found = self.navigator().setCurrentSchemaPath(path)
        if found:
            self.lineEdit().setText(path)
        else:
            self.lineEdit().setText('')
    
    def setTableType(self, tableType):
        """
        Sets the table type associated with this navigator.
        
        :param      tableType | <subclass of orb.Table>
        """
        self.navigator().setTableType(tableType)
        completer = XJoinCompleter(self.navigator().model(), self)
        completer.setCompletionMode(XJoinCompleter.InlineCompletion)
        self.setCompleter(completer)
    
    def showPopup(self):
        """
        Displays the popup associated with this navigator.
        """
        nav = self.navigator()
        
        nav.move(self.mapToGlobal(QPoint(0, self.height())))
        nav.resize(400, 250)
        nav.show()
    
    def tableType(self):
        """
        Returns the table type associated with this navigator.
        
        :return     <subclass of orb.Table> || None
        """
        return self.navigator().tableType()

__designer_plugins__ = [XOrbColumnNavigator, XOrbColumnNavigatorBox]