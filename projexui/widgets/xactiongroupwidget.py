#!/usr/bin/python

""" Defines the XActionGroupWidget class. """

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
     background-color: qlineargradient(x1: %(x1)s, 
                                       y1: %(y1)s, 
                                       x2: %(x2)s, 
                                       y2: %(y2)s,
                                       stop: 0 %(unchecked_clr)s, 
                                       stop: 1 %(unchecked_clr_alt)s);
 }

 QToolButton:pressed, QToolButton:checked, QToolButton:hover {
     background-color: qlineargradient(x1: %(x1)s, 
                                       y1: %(y1)s, 
                                       x2: %(x2)s, 
                                       y2: %(y2)s,
                                       stop: 0 %(checked_clr)s, 
                                       stop: 1 %(checked_clr_alt)s);
 }
 """

class XActionGroupWidget(QWidget):
    """
    ~~>[img:widgets/xactiongroupwidget.png]

    The XActionGroupWidget class provides a simple class for creating a 
    multi-checkable tool button based on QActions and QActionGroups.

    === Example Usage ===

    |>>> from projexui.widgets.xactiongroupwidget import XActionGroupWidget
    |>>> import projexui
    |
    |>>> # create the widget
    |>>> widget = projexui.testWidget(XActionGroupWidget)
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
    
    def __init__( self, parent = None ):
        super(XActionGroupWidget, self).__init__( parent )
        
        # define custom properties
        self._actionGroup   = None
        self._padding       = 5
        self._cornerRadius  = 10
        
        # set default properties
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred )
        self.setLayout(layout)
        
        # create connections
    
    def actionGroup( self ):
        """
        Returns the action group linked with this widget.
        
        :return     <QActionGroup>
        """
        return self._actionGroup
    
    def addAction( self, action ):
        """
        Adds the inputed action to this widget's action group.  This will auto-\
        create a new group if no group is already defined.
        
        :param      action | <QAction> || <str>
        
        :return     <QAction>
        """
        if not isinstance(action, QAction):
            action_name = nativestring(action)
            action = QAction(action_name, self)
            action.setObjectName(action_name)
        
        action.setCheckable(True)
        
        if ( not self._actionGroup ):
            self._actionGroup = QActionGroup(self)
            action.setChecked(True)
            
        self._actionGroup.addAction(action)
        self.reset()
        return action
    
    def colorString( self, clr ):
        """
        Renders the inputed color to an RGB string value.
        
        :return     <str>
        """
        return 'rgb(%s, %s, %s)' % (clr.red(), clr.green(), clr.blue())
    
    def cornerRadius( self ):
        """
        Returns the corner radius for this widget.
        
        :return     <int>
        """
        return self._cornerRadius
    
    def currentAction( self ):
        """
        Returns the action that is currently checked in the system.
        
        :return     <QAction> || None
        """
        if ( not self._actionGroup ):
            return None
            
        for act in self._actionGroup.actions():
            if ( act.isChecked() ):
                return act
        return None
    
    def direction( self ):
        """
        Returns the direction for this widget.
        
        :return     <QBoxLayout::Direction>
        """
        return self.layout().direction()
    
    def findAction( self, text ):
        """
        Looks up the action based on the inputed text.
        
        :return     <QAction> || None
        """
        for action in self.actionGroup().actions():
            if ( text in (action.objectName(), action.text()) ):
                return action
        return None
    
    def padding( self ):
        """
        Returns the button padding amount for this widget.
        
        :return     <int>
        """
        return self._padding
    
    def reset( self ):
        """
        Resets the user interface buttons for this widget.
        """
        # clear previous widgets
        for btn in self.findChildren(QToolButton):
            btn.close()
            btn.setParent(None)
            btn.deleteLater()
        
        # determine coloring options
        palette             = self.palette()
        unchecked           = palette.color(palette.Button)
        
        # determine if this is a dark or light scheme
        avg = (unchecked.red() + unchecked.green() + unchecked.blue()) / 3.0
        if ( avg < 140 ):
            checked             = unchecked.lighter(115)
            
            checked_clr         = self.colorString(unchecked.lighter(120))
            border_clr          = self.colorString(unchecked.darker(140))
            unchecked_clr       = self.colorString(checked.lighter(140))
            unchecked_clr_alt   = self.colorString(checked.lighter(120))
            checked_clr_alt     = self.colorString(unchecked)
        else:
            checked             = unchecked.lighter(120)
            
            checked_clr         = self.colorString(unchecked)
            border_clr          = self.colorString(unchecked.darker(160))
            unchecked_clr       = self.colorString(checked)
            unchecked_clr_alt   = self.colorString(checked.darker(130))
            checked_clr_alt     = self.colorString(unchecked.darker(120))
        
        # define the stylesheet options
        options = {}
        options['top_left_radius']      = 0
        options['top_right_radius']     = 0
        options['bot_left_radius']      = 0
        options['bot_right_radius']     = 0
        options['border_color']         = border_clr
        options['checked_clr']          = checked_clr
        options['checked_clr_alt']      = checked_clr_alt
        options['unchecked_clr']        = unchecked_clr
        options['unchecked_clr_alt']    = unchecked_clr_alt
        options['padding_top']          = 1
        options['padding_bottom']       = 1
        options['padding_left']         = 1
        options['padding_right']        = 1
        
        horiz = self.direction() in (QBoxLayout.LeftToRight, 
                                     QBoxLayout.RightToLeft)
        
        if ( horiz ):
            options['x1'] = 0
            options['y1'] = 0
            options['x2'] = 0
            options['y2'] = 1
        else:
            options['x1'] = 0
            options['y1'] = 0
            options['x2'] = 1
            options['y2'] = 1
        
        actions = self.actionGroup().actions()
        count = len(actions)
        for i, action in enumerate(actions):
            btn = QToolButton(self)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setDefaultAction(action)
            self.layout().insertWidget(i, btn)
            
            options['top_left_radius']  = 1
            options['bot_left_radius']  = 1
            options['top_right_radius'] = 1
            options['bot_right_radius'] = 1
            
            if ( horiz ):
                options['padding_left']     = self._padding
                options['padding_right']    = self._padding
            else:
                options['padding_top']      = self._padding
                options['padding_bottom']   = self._padding
            
            if ( not i ):
                if ( horiz ):
                    options['top_left_radius'] = self.cornerRadius()
                    options['bot_left_radius'] = self.cornerRadius()
                    options['padding_left']    += self.cornerRadius() / 3.0
                else:
                    options['top_left_radius'] = self.cornerRadius()
                    options['top_right_radius'] = self.cornerRadius()
                    options['padding_top']     += self.cornerRadius() / 3.0
                    
            elif ( i == count - 1 ):
                if ( horiz ):
                    options['top_right_radius'] = self.cornerRadius()
                    options['bot_right_radius'] = self.cornerRadius()
                    options['padding_right']    += self.cornerRadius() / 3.0
                else:
                    options['bot_left_radius']  = self.cornerRadius()
                    options['bot_right_radius'] = self.cornerRadius()
                    options['padding_bottom']   += self.cornerRadius() / 3.0
            
            btn.setStyleSheet(TOOLBUTTON_STYLE % options)
            btn.setAutoFillBackground(True)
    
    def setActionGroup( self, actionGroup ):
        """
        Sets the action group for this widget to the inputed action group.
        
        :param      actionGroup | <QActionGroup>
        """
        self._actionGroup = actionGroup
        self.reset()
    
    def setCornerRadius( self, radius ):
        """
        Sets the corner radius value for this widget to the inputed radius.
        
        :param      radius | <int>
        """
        self._cornerRadius = radius
    
    def setDirection( self, direction ):
        """
        Sets the direction that this group widget will face.
        
        :param      direction | <QBoxLayout::Direction>
        """
        self.layout().setDirection(direction)
        self.reset()
    
    def setPadding( self, padding ):
        """
        Sets the padding amount for this widget's button set.
        
        :param      padding | <int>
        """
        self._padding = padding
        self.reset()

__designer_plugins__ = [XActionGroupWidget]