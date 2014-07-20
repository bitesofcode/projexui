""" Defines the grouping class for the orb tree widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt.QtCore import QSize, Qt
from projexui.qt.QtGui  import QIcon, QApplication

from projexui.widgets.xtreewidget import XTreeWidgetItem
from projexui import resources

from .xorbrecorditem import XOrbRecordItem

from orb import RecordSet

class XOrbGroupItem( XTreeWidgetItem ):
    def __init__(self, parent, grp, records=None, nextLevels=None):
        super(XOrbGroupItem, self).__init__(parent)
        
        # define custom properties
        self._loaded    = False
        self._recordSet = None
        self._nextLevels = nextLevels
        
        # set local properties
        self.setFixedHeight(22)
        self.setText(0, nativestring(grp))
        self.setFirstColumnSpanned(True)
        self.setChildIndicatorPolicy(self.ShowIndicator)
        
        # setup the icons
        icon = QIcon(resources.find('img/treeview/folder.png'))
        expanded_icon = QIcon(resources.find('img/treeview/folder_open.png'))
        self.setIcon(0, icon)
        self.setExpandedIcon(0, expanded_icon)
        
        # load the records for this group
        if isinstance(records, RecordSet):
            self.setRecordSet(records)
        elif type(records) in (dict, list, tuple):
            self.loadRecords(records)
    
    def findItemsByState(self, state):
        out = []
        for c in range(self.childCount()):
            child = self.child(c)
            out += child.findItemsByState(state)
        return out
    
    def loadRecords(self, records):
        """
        Loads the inputed records as children to this item.
        
        :param      records | [<orb.Table>, ..] || {<str> sub: <variant>, .. }
        """
        self.setChildIndicatorPolicy(self.DontShowIndicatorWhenChildless)
        self._loaded = True
        
        if records is None:
            return
        
        # load sub-groups if desired
        if self._nextLevels and RecordSet.typecheck(records):
            level = self._nextLevels[0]
            sublevels = self._nextLevels[1:]
            
            records = records.grouped(level)
            
        elif RecordSet.typecheck(records):
            sublevels = None
            records = records.all()
        
        else:
            sublevels = None
        
        # load a child set of groups
        if type(records) == dict:
            try:
                generator = self.treeWidget().createGroupItem
                cls = None
            except AttributeError:
                generator = None
                cls = type(self)
                
            for subgroup, subrecords in records.items():
                if generator:
                    generator(subgroup, subrecords, sublevels, self)
                elif cls:
                    cls(self, subgroup, subrecords, sublevels)
        
        # load records
        else:
            try:
                generator = self.treeWidget().createRecordItem
                cls = None
            except AttributeError:
                generator = None
                cls = XOrbRecordItem
            
            cls = self.treeWidget().createRecordItem
            for record in records:
                if generator:
                    generator(record, self)
                elif cls:
                    cls(self, record)
    
    def load(self):
        """
        Loads the records from the query set linked with this item.
        """
        if self._loaded:
            return
        
        rset = self.recordSet()
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.loadRecords(rset)
        QApplication.restoreOverrideCursor()
    
    def recordSet(self):
        """
        Returns the record set that is linked with this grouping item.
        
        :return     <orb.RecordSet>
        """
        return self._recordSet
    
    def setRecordSet(self, recordSet):
        """
        Sets the record set that is linked with this grouping item.
        
        :param      recordSet | <orb.RecordSet>
        """
        self._recordSet = recordSet