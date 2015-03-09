""" Defines the different plugins that will be used for this widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import glob
import logging
import os.path

logger  = logging.getLogger(__name__)
widgets = {}

_loaded = False
def init():
    global _loaded
    if ( _loaded ):
        return
        
    _loaded   = True
    path      = os.path.dirname(__file__) + '/*.py'
    filenames = glob.glob(path)
    
    for filename in filenames:
        modname = os.path.basename(filename).split('.')[0]
        if ( modname == '__init__' ):
            continue
        
        package = '%s.%s' % (__name__, modname)
        try:
            __import__(package)
        except ImportError:
            logger.warning('Could not load %s.' % package)

