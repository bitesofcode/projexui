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

class XDatasetAxis(XChartAxis):
    def calculateValues(self):
        """
        Overloads the calculate values method to calculate the values for
        this axis based on the minimum and maximum values, and the number
        of steps desired.
        
        :return     [<variant>, ..]
        """
        chart = self.chart()
        if not chart:
            return super(XDatasetAxis, self).calculateValues()
        else:
            values = []
            for dataset in chart.datasets():
                values.append(dataset.name())
            values.sort()
            return values