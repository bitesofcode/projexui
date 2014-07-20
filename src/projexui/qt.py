"""
This module is a placeholder for the xqt library.  There was a use
in breaking out the Qt wrapping system to its own project.  This
module is kept for backward compatibility
"""

import os
import sys

if 'PROJEXUI_QT_WRAPPER' in os.environ:
    os.environ['XQT_WRAPPER'] = os.environ['PROJEXUI_QT_WRAPPER']

from xqt import *

for key, value in sys.modules.items():
    if key.startswith('xqt'):
        sys.modules[key.replace('xqt', 'projexui.qt')] = value