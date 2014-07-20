#!/usr/bin/python

""" 
Defines a chart widget for use in displaying data. 

:note   This widget replaces the deprecated XChartWidget class.
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

from .xchart import XChart
from .xchartdataset import XChartDataset
from .xchartaxis import XChartAxis

# import axis plugins
from .axes.xnumberaxis import XNumberAxis
from .axes.xdatetimeaxis import XDatetimeAxis
from .axes.xdatasetaxis import XDatasetAxis

# import bar chart plugins
from .renderers.xbarrenderer    import XBarRenderer
from .renderers.xlinerenderer   import XLineRenderer
from .renderers.xpierenderer    import XPieRenderer
from .renderers.xdonutrenderer  import XDonutRenderer

__designer_plugins__ = [XChart]