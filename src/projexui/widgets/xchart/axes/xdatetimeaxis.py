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

import datetime
from projexui.widgets.xchart.xchartaxis import XChartAxis

class XDatetimeAxis(XChartAxis):
    def __init__(self, *args, **kwds):
        super(XDatetimeAxis, self).__init__(*args, **kwds)
        
        # set default properties
        year = datetime.date.today().year
        self.setDynamicScalingEnabled(True)
        self.setLabelFormat('{0:%b}')
        self.setMinimum(datetime.datetime(year, 1, 1))
        self.setMaximum(datetime.datetime(year, 12, 31, 23, 59, 59))
        
        values = []
        for i in range(11):
            values.append(datetime.datetime(year, i+1, 1))
        values.append(self.maximum())
        self.setValues(values)
    
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
        seconds = (self.maximum() - self.minimum()).total_seconds()
        step = datetime.timedelta(0, int(round(float(seconds) / max_labels)))
        
        values = []
        value = self.minimum()
        while value <= self.maximum():
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
        
        # round the max value to sync with the values in the grid
        total_seconds = (max_val - min_val).total_seconds()
        value_seconds = (value - min_val).total_seconds()
        
        if value < min_val:
            return 0.0
        elif max_val < value:
            return 1.0
        
        try:
            perc = value_seconds / float(total_seconds)
        except ZeroDivisionError:
            perc = 0.0
        
        return perc
    
    def sum(self, values):
        """
        Calculates the total values for the inputed values.
        
        :return     <int>
        """
        values = sorted(values)
        try:
            return (values[-1] - values[0]).total_seconds()
        except IndexError, TypeError:
            return 0
    
    def valueAt(self, percent):
        """
        Returns the value the percent represents between the minimum and
        maximum for this axis.
        
        :param      value | <int> || <float>
        
        :return     <float>
        """
        min_val = self.minimum()
        max_val = self.maximum()
        
        if percent < 0:
            return min_val
        elif 1 < percent:
            return max_val
        
        # round the max value to sync with the values in the grid
        total_seconds = (max_val - min_val).total_seconds()
        perc_seconds = max(min(percent, 1.0), 0.0) * total_seconds
        
        return max_val + datetime.timedelta(0, perc_seconds)