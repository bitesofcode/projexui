""" Defines the hook required for the PyInstaller to use projexui with it. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

__all__ = ['hiddenimports', 'datas', 'excludes']

import os
import projex.pyi

if 'PROJEXUI_QT_WRAPPER' in os.environ:
    os.environ.setdefault('XQT_WRAPPER', os.environ['PROJEXUI_QT_WRAPPER'])

from xqt.pyi_hook import hiddenimports as xqt_hidden
from xqt.pyi_hook import datas as xqt_datas
from xqt.pyi_hook import excludes as xqt_excludes

basepath = os.path.dirname(__file__)
m_hidden, m_data = projex.pyi.collect(basepath)

if os.environ.get('PROJEXUI_BUILD_UI') != 'False':
    import projexui
    projexui.generateUiClasses(basepath)

hiddenimports = m_hidden + xqt_hidden
datas = m_data + xqt_datas
excludes = xqt_excludes

if os.environ.get('PROJEXUI_BUILD_UI') != 'False':
    datas = filter(lambda x: not x[0].endswith('.ui'), datas)