#!/usr/bin/python

"""
Defines a Qt wizard that will step a user through creating a Scaffold
instance.

:sa     <projex.scaffold.Scaffold>
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

#------------------------------------------------------------------------------

import os
import re
import projexui

from projex.text import nativestring
from projexui.qt import wrapVariant, unwrapVariant, QtCore, QtGui
from projexui.widgets.xtreewidget import XTreeWidget, XTreeWidgetItem

from projexui.widgets.xtextedit import XTextEdit
from projexui.widgets.xcombobox import XComboBox
from projexui.widgets.xfilepathedit import XFilepathEdit
from projexui.widgets.xlineedit import XLineEdit
from projexui.widgets.xiconbutton import XIconButton

class XScaffoldWizard(QtGui.QWizard):
    """ """
    def __init__(self, scaffold, parent=None):
        super(XScaffoldWizard, self).__init__(parent)
        
        # define custom properties
        self.setWindowTitle('{0} Scaffold Wizard'.format(scaffold.name()))
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        
        self.addPage(XScaffoldPropertiesPage(scaffold, self))
        self.addPage(XScaffoldStructurePage(scaffold, self))


#----------------------------------------------------------------------

class XScaffoldPropertiesPage(QtGui.QWizardPage):
    def __init__(self, scaffold, parent=None):
        super(XScaffoldPropertiesPage, self).__init__(parent)
        
        # setup the scaffolding options
        self._scaffold = scaffold
        
        self.setTitle('Properties')
        self.setSubTitle('Setup scaffold properties')
        
        if scaffold.uifile():
            projexui.loadUi(__file__, self, scaffold.uifile())
        else:
            layout = QtGui.QFormLayout()
            
            for prop in scaffold.properties():
                # define the text
                text = prop.label
                if prop.required:
                    text += '*'
                text += ':'
                
                # create a checkbox
                if prop.type == 'bool':
                    widget = QtGui.QCheckBox(self)
                    widget.setProperty('propertyName', wrapVariant(prop.name))
                    widget.setText(text.strip(':'))
                    layout.addRow(None, widget)
                
                # create a float
                elif prop.type == 'int':
                    lbl = QtGui.QLabel(text, self)
                    widget = QtGui.QSpinBox(self)
                    widget.setProperty('propertyName', wrapVariant(prop.name))
                    layout.addRow(lbl, widget)
                
                # create a double
                elif prop.type == 'float':
                    lbl = QtGui.QLabel(text, self)
                    widget = QtGui.QDoubleSpinBox(self)
                    widget.setProperty('propertyName', wrapVariant(prop.name))
                    layout.addRow(lbl, widget)
                
                # create a text edit
                elif prop.type == 'text':
                    lbl = QtGui.QLabel(text, self)
                    widget = XTextEdit(self)
                    widget.setProperty('propertyName', wrapVariant(prop.name))
                    layout.addRow(lbl, widget)

                # create a filepath
                elif prop.type == 'file':
                    lbl = QtGui.QLabel(text, self)
                    widget = XFilepathEdit(self)

                # create an icon
                elif prop.type == 'icon':
                    widget = XIconButton(self)
                    layout.addRow(lbl, widget)

                # create a line edit
                else:
                    lbl = QtGui.QLabel(text, self)
                    
                    if prop.choices:
                        widget = XComboBox(self)
                        widget.setProperty('dataType', 'string')
                        widget.addItems([''] + prop.choices)
                    else:
                        widget = XLineEdit(self)
                        
                        if prop.regex:
                            regexp = QtCore.QRegExp(prop.regex)
                            validator = QtGui.QRegExpValidator(regexp, widget)
                            widget.setValidator(validator)
                    
                    widget.setProperty('propertyName', wrapVariant(prop.name))
                    layout.addRow(lbl, widget)
            
            self.setLayout(layout)

        for prop, widget in self.propertyWidgetMap().items():
            if prop.default is not None:
                try:
                    widget.setHint(prop.default)
                except AttributeError:
                    projexui.setWidgetValue(widget, prop.default)

    def propertyWidgetMap(self):
        """
        Returns the mapping for this page between its widgets and its
        scaffold property.
        
        :return     {<projex.scaffold.Property>: <QtGui.QWidget>, ..}
        """
        out = {}
        scaffold = self.scaffold()
        
        # initialize the scaffold properties
        for widget in self.findChildren(QtGui.QWidget):
            propname = unwrapVariant(widget.property('propertyName'))
            if not propname: continue
            
            prop = scaffold.property(propname)
            if not prop: continue
            
            out[prop] = widget

        return out

    def scaffold(self):
        """
        Returns the scaffold associated with this wizard.
        
        :return     <projex.scaffold.Scaffold>
        """
        return self._scaffold

    def validatePage(self):
        """
        Validates the page against the scaffold information, setting the
        values along the way.
        """
        widgets = self.propertyWidgetMap()
        failed = ''
        for prop, widget in widgets.items():
            val, success = projexui.widgetValue(widget)
            
            if success:
                # ensure we have the required values
                if not val and not (prop.type == 'bool' and val is False):
                    if prop.default:
                        val = prop.default
                    elif prop.required:
                        msg = '{0} is a required value'.format(prop.label)
                        failed = msg
                        break
                
                # ensure the values match the required expression
                elif prop.regex and not re.match(prop.regex, nativestring(val)):
                    msg = '{0} needs to be in the format {1}'.format(prop.label,
                                                                 prop.regex)
                    failed = msg
                    break
                
                prop.value = val
            else:
                msg = 'Failed to get a proper value for {0}'.format(prop.label)
                failed = msg
                break
        
        if failed:
            QtGui.QMessageBox.warning(None, 'Properties Failed', failed)
            return False

        return True

#----------------------------------------------------------------------

class XScaffoldElementItem(XTreeWidgetItem):
    def __init__(self, parent, element):
        super(XScaffoldElementItem, self).__init__(parent)
        
        # define custom properties
        self._element = element
        
        # setup properties
        self.setFixedHeight(20)
        self.setText(0, element.get('name', ''))
        self.update(element.get('enabled', 'True') == 'True')
        
        # setup the icon for this item
        folder_ico = QtGui.QIcon(projexui.resources.find('img/folder.png'))
        file_ico = QtGui.QIcon(projexui.resources.find('img/file.png'))
        if element.tag == 'folder':
            self.setIcon(0, folder_ico)
        else:
            self.setIcon(0, file_ico)
        
        # create sub-items
        for xchild in element:
            XScaffoldElementItem(self, xchild)
        
        self.setExpanded(element.get('expand', 'True') == 'True')

    def element(self):
        """
        Returns the element associated with this item.
        
        :return     <xml.etree.ElementTree.Element>
        """
        return self._element

    def save(self):
        """
        Saves the state for this item to the scaffold.
        """
        enabled = self.checkState(0) == QtCore.Qt.Checked
        self._element.set('name', nativestring(self.text(0)))
        self._element.set('enabled', nativestring(enabled))
        
        for child in self.children():
            child.save()

    def update(self, enabled=None):
        """
        Updates this item based on the interface.
        """
        if enabled is None:
            enabled = self.checkState(0) == QtCore.Qt.Checked
        elif not enabled or self._element.get('enabled', 'True') != 'True':
            self.setCheckState(0, QtCore.Qt.Unchecked)
        else:
            self.setCheckState(0, QtCore.Qt.Checked)
        
        if enabled:
            self.setForeground(0, QtGui.QBrush())
        else:
            self.setForeground(0, QtGui.QBrush(QtGui.QColor('lightGray')))

        for child in self.children():
            child.update(enabled)

#----------------------------------------------------------------------

class XScaffoldStructurePage(QtGui.QWizardPage):
    def __init__(self, scaffold, parent=None):
        super(XScaffoldStructurePage, self).__init__(parent)
        
        # setup the scaffolding options
        self._scaffold = scaffold
        self._structure = None
        
        projexui.loadUi(__file__, self)
        
        path = QtGui.QApplication.clipboard().text()
        if not os.path.isdir(path):
            path = QtCore.QDir.currentPath()
        
        self.uiOutputPATH.setFilepath(path)
        self.uiStructureTREE.itemChanged.connect(self.updateItems)

    def initializePage(self):
        """
        Initializes the page based on the current structure information.
        """
        tree = self.uiStructureTREE
        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        self.uiStructureTREE.clear()
        xstruct = self.scaffold().structure()
        
        self._structure = xstruct
        for xentry in xstruct:
            XScaffoldElementItem(tree, xentry)
        
        tree.blockSignals(False)
        tree.setUpdatesEnabled(True)

    def scaffold(self):
        """
        Returns the scaffold associated with this wizard.
        
        :return     <projex.scaffold.Scaffold>
        """
        return self._scaffold

    def validatePage(self):
        """
        Finishes up the structure information for this wizard by building
        the scaffold.
        """
        path = self.uiOutputPATH.filepath()
        
        for item in self.uiStructureTREE.topLevelItems():
            item.save()
        
        try:
            self.scaffold().build(path, self._structure)
        except Exception, err:
            QtGui.QMessageBox.critical(None, 'Error Occurred', nativestring(err))
            return False

        return True

    def updateItems(self, item):
        tree = self.uiStructureTREE
        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        item.update()
        tree.blockSignals(False)
        tree.setUpdatesEnabled(True)
