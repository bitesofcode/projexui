#!/usr/bin/python

""" Defines the XSplitButton class. """

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

from projexui.qt       import Signal, Property
from projexui.qt.QtCore import QSize, QStringList
from projexui.qt.QtGui import QAction,\
                              QActionGroup,\
                              QBoxLayout,\
                              QSizePolicy,\
                              QToolButton,\
                              QWidget

import projexui.resources

TOOLBUTTON_STYLE = """
QToolButton { /* all types of tool button */
    border: 1px solid %(border_color)s;
    border-top-left-radius: %(top_left_radius)ipx;
    border-top-right-radius: %(top_right_radius)ipx;
    border-bottom-left-radius: %(bot_left_radius)ipx;
    border-bottom-right-radius: %(bot_right_radius)ipx;
    padding-top: %(padding_top)ipx;
    padding-left: %(padding_left)ipx;
    padding-right: %(padding_right)ipx;
    padding-bottom: %(padding_bottom)ipx;
    color: %(unchecked_fg)s;
    background-color: qlineargradient(x1: %(x1)s, 
                                      y1: %(y1)s, 
                                      x2: %(x2)s, 
                                      y2: %(y2)s,
                                      stop: 0 %(unchecked_bg)s, 
                                      stop: 1 %(unchecked_bg_alt)s);
}

QToolButton:checked, QToolButton:hover {
    color: %(checked_fg)s;
    background-color: qlineargradient(x1: %(x1)s, 
                                      y1: %(y1)s, 
                                      x2: %(x2)s, 
                                      y2: %(y2)s,
                                      stop: 0 %(checked_bg)s, 
                                      stop: 1 %(checked_bg_alt)s);
}
QToolButton:pressed {
    color: %(checked_fg)s;
    background-color: qlineargradient(x1: %(x1)s, 
                                      y1: %(y1)s, 
                                      x2: %(x2)s, 
                                      y2: %(y2)s,
                                      stop: 0 %(checked_bg_alt)s, 
                                      stop: 1 %(checked_bg)s);
}
 """

class XSplitButton(QWidget):
    """
    ~~>[img:widgets/xsplitbutton.png]

    The XSplitButton class provides a simple class for creating a 
    multi-checkable tool button based on QActions and QActionGroups.

    === Example Usage ===

    |>>> from projexui.widgets.xsplitbutton import XSplitButton
    |>>> import projexui
    |
    |>>> # create the widget
    |>>> widget = projexui.testWidget(XSplitButton)
    |
    |>>> # add some actions (can be text or a QAction)
    |>>> widget.addAction('Day')
    |>>> widget.addAction('Month')
    |>>> widget.addAction('Year')
    |
    |>>> # create connections
    |>>> def printAction(act): print act.text()
    |>>> widget.actionGroup().triggered.connect(printAction)
    """
    
    __designer_icon__ = projexui.resources.find('img/ui/multicheckbox.png')
    
    clicked                 = Signal()
    currentActionChanged    = Signal(object)
    currentIndexChanged     = Signal(int)
    hovered                 = Signal(object)
    triggered               = Signal(object)
    
    def __init__( self, parent = None ):
        super(XSplitButton, self).__init__( parent )
        
        # define custom properties
        self._actionGroup   = QActionGroup(self)
        self._padding       = 5
        self._cornerRadius  = 10
        self._checkable     = True
        
        # set default properties
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setLayout(layout)
        self.clear()
        
        # create connections
        self._actionGroup.hovered.connect(self.emitHovered)
        self._actionGroup.triggered.connect(self.emitTriggered)
    
    def actions(self):
        """
        Returns a list of the actions linked with this widget.
        
        :return     [<QAction>, ..]
        """
        return self._actionGroup.actions()
    
    def actionTexts(self):
        """
        Returns a list of the action texts for this widget.
        
        :return     [<str>, ..]
        """
        return map(lambda x: x.text(), self._actionGroup.actions())
    
    def actionGroup(self):
        """
        Returns the action group linked with this widget.
        
        :return     <QActionGroup>
        """
        return self._actionGroup
    
    def addAction(self, action, checked=None, autoBuild=True):
        """
        Adds the inputed action to this widget's action group.  This will auto-\
        create a new group if no group is already defined.
        
        :param      action | <QAction> || <str>
        
        :return     <QAction>
        """
        # clear the holder
        actions = self._actionGroup.actions()
        if actions and actions[0].objectName() == 'place_holder':
            self._actionGroup.removeAction(actions[0])
            actions[0].deleteLater()
        
        # create an action from the name
        if not isinstance(action, QAction):
            action_name = nativestring(action)
            action = QAction(action_name, self)
            action.setObjectName(action_name)
            action.setCheckable(self.isCheckable())
            
            # auto-check the first option
            if checked or (not self._actionGroup.actions() and checked is None):
                action.setChecked(True)
        
        elif self.isCheckable():
            action.setCheckable(True)
            if not self.currentAction():
                action.setChecked(True)
        
        self._actionGroup.addAction(action)
        
        if autoBuild:
            self.rebuild()
        
        return action
    
    def clear(self, autoBuild=True):
        """
        Clears the actions for this widget.
        """
        for action in self._actionGroup.actions():
            self._actionGroup.removeAction(action)
        
        action = QAction('', self)
        action.setObjectName('place_holder')
        self._actionGroup.addAction(action)
        if autoBuild:
            self.rebuild()
    
    def cornerRadius( self ):
        """
        Returns the corner radius for this widget.
        
        :return     <int>
        """
        return self._cornerRadius
    
    def count(self):
        """
        Returns the number of actions associated with this button.
        
        :return     <int>
        """
        actions = self._actionGroup.actions()
        if len(actions) == 1 and actions[0].objectName() == 'place_holder':
            return 0
        
        return len(actions)
    
    def currentAction(self):
        """
        Returns the action that is currently checked in the system.
        
        :return     <QAction> || None
        """
        return self._actionGroup.checkedAction()
    
    def direction( self ):
        """
        Returns the direction for this widget.
        
        :return     <QBoxLayout::Direction>
        """
        return self.layout().direction()
    
    def emitClicked(self):
        """
        Emits the clicked signal whenever any of the actions are clicked.
        """
        if not self.signalsBlocked():
            self.clicked.emit()
    
    def emitHovered(self, action):
        """
        Emits the hovered action for this widget.
        
        :param      action | <QAction>
        """
        if not self.signalsBlocked():
            self.hovered.emit(action)
    
    def emitTriggered(self, action):
        """
        Emits the triggered action for this widget.
        
        :param      action | <QAction>
        """
        self.currentActionChanged.emit(action)
        self.currentIndexChanged.emit(self.indexOf(action))
        
        if not self.signalsBlocked():
            self.triggered.emit(action)
    
    def findAction(self, text):
        """
        Looks up the action based on the inputed text.
        
        :return     <QAction> || None
        """
        for action in self.actionGroup().actions():
            if text in (action.objectName(), action.text()):
                return action
        return None
    
    def indexOf(self, action):
        """
        Returns the index of the inputed action.
        
        :param      action | <QAction> || None
        
        :return     <int>
        """
        for i, act in enumerate(self.actionGroup().actions()):
            if action in (act, act.objectName(), act.text()):
                return i
        return -1
    
    def isCheckable(self):
        """
        Returns whether or not the actions within this button should be
        checkable.
        
        :return     <bool>
        """
        return self._checkable
    
    def padding( self ):
        """
        Returns the button padding amount for this widget.
        
        :return     <int>
        """
        return self._padding
    
    def rebuild( self ):
        """
        Rebuilds the user interface buttons for this widget.
        """
        self.setUpdatesEnabled(False)
        
        # sync up the toolbuttons with our actions
        actions = self._actionGroup.actions()
        btns    = self.findChildren(QToolButton)
        horiz   = self.direction() in (QBoxLayout.LeftToRight, 
                                       QBoxLayout.RightToLeft)
        
        # remove unnecessary buttons
        if len(actions) < len(btns):
            rem_btns = btns[len(actions)-1:]
            btns = btns[:len(actions)]
            
            for btn in rem_btns:
                btn.close()
                btn.setParent(None)
                btn.deleteLater()
        
        # create new buttons
        elif len(btns) < len(actions):
            for i in range(len(btns), len(actions)):
                btn = QToolButton(self)
                btn.setAutoFillBackground(True)
                btns.append(btn)
                self.layout().addWidget(btn)
                
                btn.clicked.connect(self.emitClicked)
        
        # determine coloring options
        palette      = self.palette()
        checked      = palette.color(palette.Highlight)
        checked_fg   = palette.color(palette.HighlightedText)
        unchecked    = palette.color(palette.Button)
        unchecked_fg = palette.color(palette.ButtonText)
        border       = palette.color(palette.Mid)
        
        # define the stylesheet options
        options = {}
        options['top_left_radius']      = 0
        options['top_right_radius']     = 0
        options['bot_left_radius']      = 0
        options['bot_right_radius']     = 0
        options['border_color']         = border.name()
        options['checked_fg']           = checked_fg.name()
        options['checked_bg']           = checked.name()
        options['checked_bg_alt']       = checked.darker(120).name()
        options['unchecked_fg']         = unchecked_fg.name()
        options['unchecked_bg']         = unchecked.name()
        options['unchecked_bg_alt']     = unchecked.darker(120).name()
        options['padding_top']          = 1
        options['padding_bottom']       = 1
        options['padding_left']         = 1
        options['padding_right']        = 1
        
        if horiz:
            options['x1'] = 0
            options['y1'] = 0
            options['x2'] = 0
            options['y2'] = 1
        else:
            options['x1'] = 0
            options['y1'] = 0
            options['x2'] = 1
            options['y2'] = 1
        
        # sync up the actions and buttons
        count = len(actions)
        palette = self.palette()
        font = self.font()
        for i, action in enumerate(actions):
            btn = btns[i]
            
            # assign the action for this button
            if btn.defaultAction() != action:
                # clear out any existing actions
                for act in btn.actions():
                    btn.removeAction(act)
                
                # assign the given action
                btn.setDefaultAction(action)
            
            options['top_left_radius']  = 1
            options['bot_left_radius']  = 1
            options['top_right_radius'] = 1
            options['bot_right_radius'] = 1
            
            if horiz:
                options['padding_left']     = self._padding
                options['padding_right']    = self._padding
            else:
                options['padding_top']      = self._padding
                options['padding_bottom']   = self._padding
            
            if not i:
                if horiz:
                    options['top_left_radius'] = self.cornerRadius()
                    options['bot_left_radius'] = self.cornerRadius()
                    options['padding_left']    += self.cornerRadius() / 3.0
                else:
                    options['top_left_radius'] = self.cornerRadius()
                    options['top_right_radius'] = self.cornerRadius()
                    options['padding_top']     += self.cornerRadius() / 3.0
                    
            if i == count - 1:
                if horiz:
                    options['top_right_radius'] = self.cornerRadius()
                    options['bot_right_radius'] = self.cornerRadius()
                    options['padding_right']    += self.cornerRadius() / 3.0
                else:
                    options['bot_left_radius']  = self.cornerRadius()
                    options['bot_right_radius'] = self.cornerRadius()
                    options['padding_bottom']   += self.cornerRadius() / 3.0
            
            btn.setFont(font)
            btn.setPalette(palette)
            btn.setStyleSheet(TOOLBUTTON_STYLE % options)
            if horiz:
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            else:
                btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        self.setUpdatesEnabled(True)
    
    def setActions(self, actions):
        """
        Sets the actions for this widget to th inputed list of actions.
        
        :param      [<QAction>, ..]
        """
        self.clear(autoBuild=False)
        for action in actions:
            self.addAction(action, autoBuild=False)
        self.rebuild()
    
    def setActionTexts(self, names):
        """
        Convenience method for auto-generating actions based on text names,
        sets the list of actions for this widget to the inputed list of names.
        
        :param      names | [<str>, ..]
        """
        self.setActions(names)
    
    def setActionGroup( self, actionGroup ):
        """
        Sets the action group for this widget to the inputed action group.
        
        :param      actionGroup | <QActionGroup>
        """
        self._actionGroup = actionGroup
        self.rebuild()
    
    def setCheckable(self, state):
        """
        Sets whether or not the actions within this button should be checkable.
        
        :param      state | <bool>
        """
        self._checkable = state
        for act in self._actionGroup.actions():
            act.setCheckable(state)
    
    def setCornerRadius( self, radius ):
        """
        Sets the corner radius value for this widget to the inputed radius.
        
        :param      radius | <int>
        """
        self._cornerRadius = radius
    
    def setCurrentAction(self, action):
        """
        Sets the current action for this button to the inputed action.
        
        :param      action | <QAction> || <str>
        """
        self._actionGroup.blockSignals(True)
        for act in self._actionGroup.actions():
            act.setChecked(act == action or act.text() == action)
        self._actionGroup.blockSignals(False)
    
    def setDirection( self, direction ):
        """
        Sets the direction that this group widget will face.
        
        :param      direction | <QBoxLayout::Direction>
        """
        self.layout().setDirection(direction)
        self.rebuild()
    
    def setFont(self, font):
        """
        Sets the font for this widget and propogates down to the buttons.
        
        :param      font | <QFont>
        """
        super(XSplitButton, self).setFont(font)
        self.rebuild()
    
    def setPadding( self, padding ):
        """
        Sets the padding amount for this widget's button set.
        
        :param      padding | <int>
        """
        self._padding = padding
        self.rebuild()
    
    def setPalette(self, palette):
        """
        Rebuilds the buttons for this widget since they use specific palette
        options.
        
        :param      palette | <QPalette>
        """
        super(XSplitButton, self).setPalette(palette)
        self.rebuild()
    
    def sizeHint(self):
        """
        Returns the base size hint for this widget.
        
        :return     <QSize>
        """
        return QSize(35, 22)
    
    x_actionTexts = Property(QStringList, actionTexts, setActionTexts)
    x_checkable   = Property(bool, isCheckable, setCheckable)

__designer_plugins__ = [XSplitButton]