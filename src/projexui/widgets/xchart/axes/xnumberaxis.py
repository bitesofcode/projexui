""" 
Defines a numeric axis for this chart plugin that will contain numberic values.
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

from projex.text import nativestring
from projexui.widgets.xchart.xchartaxis import XChartAxis

class XNumberAxis(XChartAxis):
    def __init__(self, *args, **kwds):
        # setup default numeric options
        kwds.setdefault('dynamicScalingEnabled', True)
        kwds.setdefault('useDynamicRange', True)
        kwds.setdefault('maximumLabelCount', 10)
        
        # initialize axis
        super(XNumberAxis, self).__init__(*args, **kwds)
        
        # define custom properties
        self._roundTo = kwds.get('roundTo', None)
    
    def calculateRange(self, values):
        """
        Calculates the range of values for this axis based on the dataset
        value amount.
        
        :param      values | [<variant>, ..]
        """
        vals = filter(lambda x: x is not None, values)
        
        try:
            min_val = min(min(vals), 0)
        except ValueError:
            min_val = 0
        
        try:
            max_val = max(max(vals), 0)
        except ValueError:
            max_val = 10
        
        ndigits  = max(len(nativestring(abs(int(min_val)))), len(nativestring(abs(int(max_val)))))
        rounding = 10 ** (ndigits - 1)
        
        self.setRoundTo(rounding)
        self.setMinimum(self.rounded(min_val, rounding))
        self.setMaximum(self.rounded(max_val, rounding))
        self.reset()
    
    def calculateValues(self):
        """
        Overloads the calculate values method to calculate the values for
        this axis based on the minimum and maximum values, and the number
        of steps desired.
        
        :return     [<variant>, ..]
        """
        if self.maximum() <= self.minimum():
            return []
        
        max_labels = self.maximumLabelCount()
        step = (self.maximum() - self.minimum()) / float(max_labels)
        step = int(round(step))
        if not step:
            step = 1
        
        values = []
        value = self.minimum()
        roundto = self.roundTo()
        first = True
        while value <= self.maximum():
            if not first and roundto < self.maximum():
                value = self.rounded(value)
            
            first = False
            values.append(value)
            value += step
        
        return values
    
    def percentAt(self, value):
        """
        Returns the percentage the value represents between the minimum and
        maximum for this axis.
        
        :param      value | <int> || <float>
        
        :return     <float>
        """
        min_val = self.minimum()
        max_val = self.maximum()
        
        if value < min_val:
            return 0.0
        elif max_val < value:
            return 1.0
        
        # round the max value to sync with the values in the grid
        max_val = self.rounded(max_val)
        
        try:
            perc = (value - min_val) / float(max_val - min_val)
        except (TypeError, ZeroDivisionError):
            return 0.0
        
        return max(min(perc, 1.0), 0.0)
    
    def percentOfTotal(self, value, values):
        """
        Calculates the percent the inputed value is in relation to the
        list of other values.
        
        :param      value  | <variant>
                    values | [<variant>, ..]
        
        :return     <float> 0.0 - 1.0
        """
        try:
            return float(value) / sum(values)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0
    
    def rounded(self, number, roundto=None):
        """
        Rounds the inputed number to the nearest value.
        
        :param      number | <int> || <float>
        """
        if roundto is None:
            roundto = self.roundTo()
        
        if not roundto:
            return number
    
        remain = number % roundto
        if remain:
            return number + (roundto - remain)
        return number
    
    def roundTo(self):
        """
        Returns the number that this should round the default values to.
        
        :return     <int>
        """
        if self._roundTo is None:
            min_val = max(self.minimum(), 1)
            max_val = max(self.maximum(), 1)
            max_labels = self.maximumLabelCount()
            
            return int(round((max_val - min_val) / float(max_labels)))
            
        return self._roundTo
    
    def setRoundTo(self, value):
        """
        Sets the number that this should round the default values to.
        
        :param      value | <int>
        """
        self._roundTo = value
    
    def sum(self, values):
        """
        Calculates the total values for the inputed values.
        
        :return     <int>
        """
        return sum(values)
        
    def valueAt(self, percent):
        """
        Returns the value the percent represents between the minimum and
        maximum for this axis.
        
        :param      value | <int> || <float>
        
        :return     <float>
        """
        min_val = self.minimum()
        max_val = self.maximum()
        
        # round the max value to sync with the values in the grid
        max_val = self.rounded(max_val)
        range_val = max(min(percent, 1.0), 0.0) * (max_val - min_val)
        return round(range_val + min_val, 1)
    