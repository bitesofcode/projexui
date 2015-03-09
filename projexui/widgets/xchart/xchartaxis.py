#!/usr/bin/python

""" 
Defines the base chart axis for calculating axis information on a chart.
"""

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

import projex.text
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QApplication, QFontMetrics

class XChartAxis(object):
    """ """
    def __init__(self, name, **options):
        # define custom properties
        self._name        = name
        self._chart       = None
        self._orientation = options.get('orientation', Qt.Horizontal)
        self._showLabels  = options.get('showLabels', True)
        self._shadeAxis   = options.get('shadeAxis', None)
        self._minimum     = options.get('minimum', None)
        self._maximum     = options.get('maximum', None)
        self._values      = options.get('values', None)
        self._labels      = options.get('labels', None)
        self._labelFont   = options.get('labelFont', QApplication.font())
        self._labelFormat = options.get('labelFormat', '{0}')
        self._hLabelPad   = options.get('horizontalLabelPadding', 6)
        self._vLabelPad   = options.get('verticalLabelPadding', 3)
        self._title       = options.get('title', '')
        
        self._maximumLabelCount = options.get('maximumLabelCount', None)
        self._minimumLabelWidth = options.get('minimumLabelWidth', 32)
        self._minimumLabelHeight = options.get('minimumLabelHeight', 22)
        
        # setup default dynamic options
        self._dynamicRange = options.get('useDynamicRange',
                                         not 'labels' in options)
        self._dynamicScalingEnabled = options.get('dynamicScalingEnabled',
                                                  False)
        
        # setup default title font
        titleFont = QApplication.font()
        titleFont.setBold(True)
        self._titleFont = options.get('titleFont', titleFont)
    
    def calculateRange(self, values):
        """
        Calculates the range of values for this axis based on the dataset
        value amount.
        
        :param      values | [<variant>, ..]
        """
        self.reset()
        self._values = list(set(values))
        self._values.sort(key=lambda x: values.index(x))
    
    def calculateValues(self):
        """
        Calculate values method to calculate the values for
        this axis based on the minimum and maximum values, and the number
        of steps desired.
        
        :return     [<variant>, ..]
        """
        if self._labels is not None:
            return self._labels[:]
        return []
    
    def chart(self):
        """
        Returns the chart that this axis is associated with.
        
        :return     <XChart> || None
        """
        return self._chart
    
    def horizontalLabelPadding(self):
        """
        Returns the padding for the horizontal direction for the labels on
        this axis.
        
        :return     <int>
        """
        return self._hLabelPad
    
    def isDynamicScalingEnabled(self):
        """
        Returns whether or not this axis supports dynamic scaling of its value
        meters.
        
        :return     <bool>
        """
        return self._dynamicScalingEnabled
    
    def labels(self):
        """
        Returns the list of labels that will be used to represent
        this axis' information.
        
        :return     [<str>, ..]
        """
        if self._labels is None:
            self._labels = map(self.labelFormat().format, self.values())
        return self._labels
    
    def labelCount(self):
        """
        Returns the label count for this axis.  If the labels have been
        defined then the length of the labels list will be provided, otherwise
        the hardcoded label count will be returned.
        
        :return     <int>
        """
        if self._labels is None:
            count = self.maximumLabelCount()
            if count is None:
                return 1
            else:
                return count
        
        return len(self._labels)
    
    def labelFormat(self):
        """
        Returns the formatter text for this axis.
        
        :return     <str>
        """
        return self._labelFormat
    
    def labelFont(self):
        """
        Returns the label font for this axis.
        
        :return     <QFont>
        """
        return self._labelFont
    
    def maximum(self):
        """
        Returns the maximum value for this axis.
        
        :return     <variant>
        """
        return self._maximum
    
    def maximumLabelCount(self):
        """
        Returns the label count for this axis.  If the labels have been
        defined then the length of the labels list will be provided, otherwise
        the hardcoded label count will be returned.
        
        :return     <int> || None
        """
        return self._maximumLabelCount
    
    def minimum(self):
        """
        Returns the minimum value for this axis.
        
        :return     <variant>
        """
        return self._minimum
    
    def minimumLabelWidth(self):
        """
        Returns the minimum label width required on this renderers font size.
        
        :param      labels | [<str>, ..]
        """
        min_w = 0
        metrics = QFontMetrics(self.labelFont())
        for label in self.labels():
            min_w = max(min_w, metrics.width(label))
        
        return max(self._minimumLabelWidth,
                   min_w + self.horizontalLabelPadding())
    
    def minimumLabelHeight(self):
        """
        Returns the minimum height that will be required based on this font size
        and labels list.
        """
        metrics = QFontMetrics(self.labelFont())
        return max(self._minimumLabelHeight,
                   metrics.height() + self.verticalLabelPadding())
    
    def name(self):
        """
        Returns the name for this axis.
        
        :return     <str>
        """
        return self._name
    
    def orientation(self):
        """
        Returns the orientation for this axis.
        
        :return     <Qt.Orientation>
        """
        return self._orientation
    
    def percentAt(self, value):
        """
        Returns the percentage where the given value lies between this rulers
        minimum and maximum values.  If the value equals the minimum, then the
        percent is 0, if it equals the maximum, then the percent is 1 - any
        value between will be a floating point.  If the ruler is a custom type,
        then only if the value matches a notch will be successful.
        
        :param      value | <variant>
        
        :return     <float>
        """
        if value is None:
            return 0.0
        
        values = self.values()
        
        try:
            return float(values.index(value)) / (len(values) - 1)
        except ValueError:
            return 0.0
        except ZeroDivisionError:
            return 1.0
    
    def percentOfTotal(self, value, values):
        """
        Calculates the percent the inputed value is in relation to the
        list of other values.
        
        :param      value  | <variant>
                    values | [<variant>, ..]
        
        :return     <float> 0.0 - 1.0
        """
        try:
            return float(values.index(value) + 1) / len(values)
        except (ZeroDivisionError, ValueError):
            return 0.0
    
    def reset(self):
        """
        Resets the information for this axis to the default values.
        """
        self._values      = None
        self._labels      = None
        
    def setChart(self, chart):
        """
        Returns the chart that this axis is associated with.
        
        :param      chart | <XChart> || None
        """
        self._chart = chart
    
    def setDynamicScalingEnabled(self, state):
        """
        Sets whether or not this axis supports dynamic scaling of its value
        meters.
        
        :param     state | <bool>
        """
        self._dynamicScalingEnabled = state
    
    def setHorizontalLabelPadding(self, padding):
        """
        Sets the padding for the horizontal direction for the labels on
        this axis.
        
        :param      padding | <int>
        """
        self._hLabelPad = padding
    
    def setLabels(self, labels):
        """
        Sets the labels for this axis to the inputed list of labels.
        
        :param      labels | [<str>, ..]
        """
        self._labels = labels[:]
    
    def setMaximumLabelCount(self, count):
        """
        Sets the target count for the number of labels that should
        be displayed for this axis.
        
        :param      count | <int>
        """
        self._maximumLabelCount = count
    
    def setLabelFont(self, font):
        """
        Sets the label font for this axis.
        
        :return     <QFont>
        """
        self._labelFont = font
    
    def setLabelFormat(self, formatter):
        """
        Sets the formatter that will be used for this axis to the inputed
        formatter.
        
        :param      formatter | <str>
        """
        self._labelFormat = formatter
    
    def setMaximum(self, maximum):
        """
        Sets the maximum value for thsi axis.
        
        :param      maximum | <variant>
        """
        self._maximum = maximum
    
    def setMinimum(self, minimum):
        """
        Sets the minimum value for this axis.
        
        :param      minimum | <variant>
        """
        self._minimum = minimum
    
    def setMinimumLabelHeight(self, height):
        """
        Returns the minimum label height for this axis.
        
        :param      height | <int>
        """
        self._minimumLabelHeight = height
    
    def setMinimumLabelWidth(self, width):
        """
        Returns the minimum label width for this axis.
        
        :param     width | <int>
        """
        self._minimumLabelWidth = width
    
    def setName(self, name):
        """
        Sets the name for this axis to the inputed name.
        
        :param      name | <str>
        """
        self._name = name
    
    def setOrientation(self, orientation):
        """
        Sets the orientation for this axis to the inputed value.
        
        :param      orientation | <Qt.Orientation>
        """
        self._orientation = orientation
    
    def setShowLabels(self, state):
        """
        Sets whether or not the labels should be shown.
        
        :param      state | <bool>
        """
        self._showLabels = state
    
    def setTitle(self, title):
        """
        Sets the title for this axis to the inputed title.
        
        :param      title | <str>
        """
        self._title = title
    
    def setTitleFont(self, font):
        """
        Sets the title font for this axis.
        
        :return     <QFont>
        """
        self._titleFont = font
    
    def setUseDynamicRange(self, state):
        """
        Sets whether or not to use a dynamic range calculation for the
        data sets.
        
        :param     state | <bool>
        """
        self._dynamicRange = state
    
    def setValues(self, values):
        """
        Sets the values for this axis to the inputed list of values.  If
        a None value is supplied, then the next time the values method is
        called, it will auto-calculate the values based on this axis'
        specifications.  Different axis plugins will calculate their
        values in different ways.
        
        :param      values | [<variant>, ..] || None
        """
        self._values = values
    
    def setVerticalLabelPadding(self, padding):
        """
        Sets the padding for the vertical direction for the labels on
        this axis.
        
        :param      padding | <int>
        """
        self._vLabelPad = padding
    
    def sum(self, values):
        """
        Calculates the total values for the inputed values.
        
        :return     <int>
        """
        return len(values)
    
    def showLabels(self):
        """
        Returns whether or not this axis should show its labels or not.
        
        :return     <bool>
        """
        return self._showLabels
    
    def title(self):
        """
        Returns the title for this axis.
        
        :return     <str>
        """
        if not self._title:
            return projex.text.pretty(self.name())
        return self._title
    
    def titleFont(self):
        """
        Returns the title font for this axis.
        
        :return     <QFont>
        """
        return self._titleFont
    
    def total(self):
        """
        Returns the total value for the viven values.
        
        :return     <variant>
        """
        return -1
    
    def useDynamicRange(self):
        """
        Returns whether or not to use a dynamic range calculation for the
        data sets.
        
        :return     <bool>
        """
        return self._dynamicRange
    
    def values(self):
        """
        Returns the values for this axis.
        
        :return     [<variant>, ..]
        """
        if self._values is None:
            self._values = self.calculateValues()
        return self._values
    
    def valueAt(self, percent):
        """
        Returns the value at the inputed percent.
        
        :param     percent | <float>
        
        :return     <variant>
        """
        values = self.values()
        if percent < 0:
            index = 0
        elif percent > 1:
            index = -1
        else:
            index = percent * (len(values) - 1)
        
        # allow some floating point errors for the index (30% left or right)
        remain = index % 1
        if remain < 0.3 or 0.7 < remain:
            try:
                return values[int(round(index))]
            except IndexError:
                return None
        return None
    
    def verticalLabelPadding(self):
        """
        Returns the padding for the vertical direction for the labels on
        this axis.
        
        :return     <int>
        """
        return self._vLabelPad