#!/usr/bin/python

""" Defines a layer for the node system. """

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

class XNodeLayer(object):
    """ 
    Defines a class for controlling objects via nodes in the node widget.
    """
    def __init__( self, scene ):
        self._scene                 = scene
        self._name                  = ''
        self._visible               = True
        self._inheritVisibility     = True
        self._editable              = True
        self._enabled               = False
        self._linkEnabledToCurrent  = False
        self._customData            = {}
        self._opacity               = 1.0
        self._zValue                = 0
        
        # nested layers
        self._parent    = None
        self._children  = []
    
    def customData(self, key, default=None):
        """
        Returns the custom data that is stored for this layer on the given key.
        
        :param      key         | <str>
                    default     | <variant>
                    
        :return     <variant>
        """
        return self._customData.get(nativestring(key), default)
    
    def isCurrent(self):
        """
        Return whether or not this layer is the current one.
        
        :return         <bool>
        """
        return self == self._scene.currentLayer()
    
    def isEditable(self):
        """
        Returns whether or not this layer is editable by the user.
        
        :return     <bool>
        """
        return self._enabled
    
    def isEnabled(self):
        """
        Return whether or not this layer is enabled and can be set as the \
        current layer.
        
        :sa     linkEnabledToCurrent
        
        :return     <bool>
        """
        
        if self._linkEnabledToCurrent:
            addtl = self.isCurrent()
        else:
            addtl = True
        
        return self._enabled and addtl
    
    def isVisible(self):
        """
        Returns whether or not this layer is visible.  If the inheritVisibility
        value is set to True, then this will look up its parent hierarchy to \
        ensure it is visible.
        
        :return     <bool>
        """
        if self._visible and self._inheritVisibility and self._parent:
            return self._parent.isVisible()
        
        return self._visible
    
    def ensureVisible(self):
        """
        Ensures that this layer is visible by turning on all parent layers \
        that it needs to based on its inheritance value.
        """
        # make sure all parents are visible
        if self._parent and self._inheritVisibility:
            self._parent.ensureVisible()
        
        self._visible = True
        self.sync()
    
    def inheritVisibility(self):
        """
        Returns whether or not this layer will inherit its visibility \
        from its parents.
        
        :return     <bool>
        """
        return self._inheritVisibility
    
    def items(self):
        """
        Returns a list of the items that are linked to this layer.
        
        :return     [<XNode> || <XNodeConnection>, ..]
        """
        from projexui.widgets.xnodewidget import XNode, XNodeConnection
        
        output = []
        for item in self.scene().items():
            if not (isinstance(item, XNode) or 
                    isinstance(item, XNodeConnection)):
                continue
                
            if item.layer() == self:
                output.append(item)
        
        return output
    
    def layerData(self):
        """
        Returns a dictionary of information about this layer that an item \
        can use to sync with.
        
        :return     <dict>
        """
        output = {}
        
        output['visible'] = self.isVisible()
        output['zValue']  = self.zValue()
        output['current'] = self.isCurrent()
        
        return output
    
    def linkEnabledToCurrent(self):
        """
        Returns whether or not the layer's enabled state will be linked to \
        whether or not it is current.
        
        :return     <bool>
        """
        return self._linkEnabledToCurrent
    
    def name(self):
        """
        Returns the name of this layer.
        
        :return     <str>
        """
        return self._name
    
    def opacity(self):
        """
        Returns the opacity amount for this layer.
        
        :return     <float>
        """
        return self._opacity
    
    def parent(self):
        """
        Returns the parent layer for this layer instance.
        
        :return     <XNodeLayer> || None
        """
        return self._parent
    
    def prepareToRemove(self):
        """
        Returns whether or not this layer is ok to remove.  By default, \
        this will just return True.  This method should be edited in a \
        subclass for custom control.
        
        :return     <bool>
        """
        return True
    
    def remove(self, removeItems=False):
        """
        Removes this layer from the scene.  If the removeItems flag is set to \
        True, then all the items on this layer will be removed as well.  \
        Otherwise, they will be transferred to another layer from the scene.
        
        :param      removeItems | <bool>
        
        :return     <bool>
        """
        # makes sure this can be removed
        if not self.prepareToRemove():
            return False
        
        items = self.items()
        
        # grabs the next layer
        if self._scene._layers:
            new_layer = self._scene._layers[0]
        else:
            new_layer = None
        
        # removes the items from the scene if flagged
        if removeItems:
            self.scene().removeItems(items)
        
        # otherwise assign to the next layer
        else:
            for item in items:
                item.setLayer(new_layer)
        
        # remove the layer from the scenes reference
        if self in self._scene._layers:
            self._scene._layers.remove(self)
        
        if new_layer:
            new_layer.setCurrent()
        
        self._scene.setModified()
        
        return True
    
    def scene(self):
        """
        Returns the scene that this layer is associated with.
        
        :return     <QGraphicsScene>
        """
        return self._scene
    
    def setCurrent(self):
        """
        Sets this layer as the current layer.
        
        :return     <bool> changed
        """
        if not self.isEditable():
            return False
            
        return self._scene.setCurrentLayer(self)
    
    def setCustomData(self, key, value):
        """
        Sets the value for this layer's custom data for the inputed key.
        
        :param      key     | <str>
                    value   | <variant>
        """
        self._customData[nativestring(key)] = value
    
    def setEditable( self, state ):
        """
        Sets whether or not this layer can be set as the current layer \
        enabling editing on the layer.
        
        :param      state | <bool>
        """
        self._enabled = state
    
    def setEnabled(self, state):
        """
        Sets whether or not this layer is enabled.
        
        :param      state | <bool>
        """
        self._enabled = state
    
    def setInheritVisibility(self, state):
        """
        Sets whether or not this node layer inherits visibility settings from \
        its parents.
        
        :param      state | <bool>
        
        :return     <bool> changed
        """
        if self._inheritVisibility == state:
            return False
            
        self._inheritVisibility = state
        self.sync()
        return True
    
    def setLinkEnabledToCurrent(self, state):
        """
        Sets whether or not this layer's enabled state will be affected by if \
        the layer is the current layer or not.
        
        :param      state | <state>
        """
        self._linkEnabledToCurrent = state
    
    def setName(self, name):
        """
        Sets the name of this layer to the inputed name.
        
        :param      name | <str>
        """
        self._name = name
    
    def setOpacity(self, opacity):
        """
        Sets the opacity amount for this layer to the inputed opacity.
        
        :param      opacity | <float>
        """
        self._opacity = opacity
    
    def setParent(self, other):
        """
        Sets the parent for this layer to the inputed layer.
        
        :param      other | <XNodeLayer> || None
        
        :return     <bool> changed
        """
        if self._parent == other:
            return False
        
        # remove this layer from its parent
        if self._parent and self in self._parent._children:
            self._parent._children.remove(self)
        
        self._parent = other
        
        # add this layer to its parent's list of children
        if self._parent and not self in self._children:
            self._parent._children.append(self)
        
        self.sync()
        
        return True
    
    def setVisible(self, state):
        """
        Sets whether or not this particular layer is visible.  Depending on \
        if the inheritVisibility property is set for this layer, it may not \
        actually affect the visible state based on its inheritance.  If you \
        want to force this layer to be visible, use the ensureVisible method.
        
        :param      state | <bool>
        
        :return     <bool> changed
        """
        # store the current state
        currvis = self.isVisible()
        
        # update the local property
        self._visible = state
        
        # check the new state
        newvis = self.isVisible()
        
        # check to see if the state has changed
        if newvis == currvis:
            return False
        
        # update the item visibility
        self.sync()
        return True
    
    def setZValue(self, zValue):
        """
        Sets the z-value for this layer to the inputed value.
        
        :param      zValue | <int>
        
        :return     <bool> changed
        """
        if zValue == self._zValue:
            return False
        
        self._zValue = zValue
        self.sync()
        return True
    
    def sync(self):
        """
        Syncs the items on this layer with the current layer settings.
        """
        layerData = self.layerData()
        for item in self.scene().items():
            try:
                if item._layer == self:
                    item.syncLayerData(layerData)
            except AttributeError:
                continue
    
    def zValue(self):
        """
        Returns the z-value of for this layer's zvalue.
        
        :return     <int>
        """
        return self._zValue

