#!/usr/bin/python

""" Provides a library of reusable user interface components. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = [
    ('Yusuke Kamiyamane',
     'Fuque icon pack from findicons.com under Creative Commons.'),
    ('Alexey Egorov',
     'Checkbox icons for XTreeWidget from findicons.com under Freeware.'),
    ('Moment Icons',
     'Folder icons from findicons.com under Creative Commons.'),
]
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__ = 'Eric Hulser'
__email__ = 'eric.hulser@gmail.com'

#------------------------------------------------------------------------------

# auto-generated version file from releasing
try:
    from ._version import __major__, __minor__, __revision__, __hash__
except ImportError:
    __major__ = 0
    __minor__ = 0
    __revision__ = 0
    __hash__ = ''

__version_info__ = (__major__, __minor__, __revision__)
__version__ = '{0}.{1}.{2}'.format(*__version_info__)


from projexui.xcommands     import *
from projexui.xwidgetvalue  import *
from projexui.xdatatype     import *

DESIGNER_MODE = 'designer.exe' in sys.executable

