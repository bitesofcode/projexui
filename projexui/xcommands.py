#!/usr/bin/python

""" Defines common commands that can be used to streamline ui development. """

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

import binascii
import imp
import os
import re
import logging
import subprocess
import sys

import projex
import projex.text
from projex.lazymodule import LazyModule
from projex.text import nativestring

from xml.etree import ElementTree

resources = LazyModule('projexui.resources')
logger = logging.getLogger(__name__)

try:
    USE_COMPILED = sys.frozen
except AttributeError:
    USE_COMPILED = False

if not USE_COMPILED:
    USE_COMPILED = os.environ.get('PROJEXUI_USE_COMPILED', '').lower() != 'false'

QT_WRAPPER = os.environ.get('PROJEXUI_QT_WRAPPER', 'PyQt4')

def ancestor(qobject, classType):
    """
    Looks up the ancestor of the inputed QObject based on the given class type.
    
    :param      qobject   | <QObject>
                classType | <subclass of QObject> || <str>
    
    :return     <subclass of QObject> || None
    """
    parent = qobject
    is_class = True
    while parent:
        if type(parent).__name__ == classType:
            return parent
        
        if is_class:
            try:
                if isinstance(parent, classType):
                    return parent
            except TypeError:
                is_class = False
        
        parent = parent.parent()
    
    return None

def buildResourceFile(rscpath, outpath=''):
    """
    Generates a Qt resource module based on the given source path.  This will
    take all the files and folders within the source and generate a new XML
    representation of that path.  An optional outpath can be provided as the
    generated resource path, by default it will be called the name of the
    source path.
    
    :param      rscpath | <str>
                buildpath | <str>
    """
    import xqt
    wrapper = QT_WRAPPER.lower()
    if not outpath:
        name = os.path.basename(rscpath).split('.')[0]
        filename = '{0}_{1}_rc.py'.format(wrapper, name)
        outpath = os.path.join(os.path.dirname(rscpath), filename)
    elif os.path.isdir(outpath):
        name = os.path.basename(rscpath).split('.')[0]
        filename = '{0}_{1}_rc.py'.format(wrapper, name)
        outpath = os.path.join(outpath, filename)
    
    # try to use Qt first, because it is so much better
    PYQT_RCC_EXE = os.environ.get('PYQT_RCC_EXE', 'pyrcc4')
    try:
        subprocess.call([PYQT_RCC_EXE, '-o', outpath, rscpath])
        used_pyqt = True
    except StandardError:
        used_pyqt = False

    if not used_pyqt:
        # make sure it is not outdated
        try:
            subprocess.call([xqt.rcc_exe, '-o', outpath, rscpath])
        except StandardError:
            exe = xqt.rcc_exe
            msg = 'You need to add the path to {0} to your system Path.'
            logger.error(msg.format(exe))
            return False
    
    # make sure we actually generated a file
    if not os.path.exists(outpath):
        logger.error('Failed to generate output file: {0}'.format(outpath))
        return False
    
    # map the output back to PySide if necessary
    if QT_WRAPPER == 'PySide' and used_pyqt:
        # clean up resource file
        with open(outpath, 'r') as f:
            data = f.read()
        
        data = data.replace('PyQt4', 'xqt')
        
        with open(outpath, 'w') as f:
            f.write(data)
    
    return True

def generateUiClasses(srcpath):
    """
    Generates the UI classes using the compilation system for Qt.
    
    :param      srcpath | <str>
    """
    import_qt(globals())
    
    for root, folders, files in os.walk(srcpath):
        found = False
        for file in files:
            name, ext = os.path.splitext(file)
            if ext != '.ui':
                continue
            
            found = True
            
            wrapper = QT_WRAPPER.lower()
            basename = file.replace('.ui', '').replace('.', '_')
            filename = '{0}_{1}_ui.py'.format(basename, wrapper)
            
            outfile = os.path.join(root, filename)
            
            # compile the ui
            f = open(outfile, 'w')
            uic.compileUi(os.path.join(root, file), f)
            f.close()
            
            # cleanup import content
            f = open(outfile, 'r')
            data = f.read()
            f.close()
            
            data = re.sub('import .*_rc', '', data)
            
            # save back out the content
            f = open(outfile, 'w')
            f.write(data)
            f.close()
        
        if found and not '__init__.py' in files:
            f = open(os.path.join(root, '__init__.py'), 'w')
            f.write('# auto created for UI import')
            f.close()

def generateResourceFile(srcpath, outpath='', buildpath='', build=True):
    """
    Generates a Qt resource file based on the given source path.  This will
    take all the files and folders within the source and generate a new XML
    representation of that path.  An optional outpath can be provided as the
    generated resource path, by default it will be called the name of the
    source path.
    
    :param      srcpath | <str>
                outpath | <str>
    """
    if not outpath:
        outpath = os.path.join(os.path.dirname(srcpath), 
                               os.path.basename(srcpath) + '.qrc')
        relpath = './%s' % os.path.basename(srcpath)
    else:
        relpath = os.path.relpath(srcpath, os.path.dirname(outpath))
    
    xml = ElementTree.Element('RCC')
    xml.set('header', 'projexui.resources')
    
    srcpath = nativestring(srcpath)
    srcpath = os.path.normpath(srcpath)
    root_prefix = os.path.basename(srcpath) + '/'
    count = len(srcpath)
    
    for root, folders, files in os.walk(srcpath):
        if not files:
            continue
        
        relpath = os.path.relpath(root, os.path.dirname(outpath))
        prefix = (root_prefix + root[count+1:].replace('\\', '/')).strip('/')
        
        xresource = ElementTree.SubElement(xml, 'qresource')
        xresource.set('prefix', prefix)
        
        for file in files:
            xfile = ElementTree.SubElement(xresource, 'file')
            xfile.set('alias', file)
            xfile.text = os.path.join(relpath, file).replace('\\', '/')
    
    projex.text.xmlindent(xml)
    xml_str = ElementTree.tostring(xml)
    
    # save the exported information
    with open(outpath, 'w') as f:
        f.write(xml_str)

    if build:
        buildResourceFile(outpath, buildpath)

def generateResourceFiles(srcpath, outpath='', buildpath='', build=True):
    """
    Generates a Qt resource file based on the given source path.  This will
    take all the files and folders within the source and generate a new XML
    representation of that path.  An optional outpath can be provided as the
    generated resource path, by default it will be called the name of the
    source path.
    
    :param      srcpath | <str>
                outpath | <str>
    """
    for filename in os.listdir(srcpath):
        rscpath = os.path.join(srcpath, filename)
        if os.path.isdir(rscpath):
            generateResourceFile(rscpath, outpath, buildpath, build)

def generatePixmap(base64_data):
    """
    Generates a new pixmap based on the inputed base64 data.
    
    :param      base64 | <str>
    """
    import_qt(globals())
    
    binary_data = binascii.a2b_base64(base64_data)
    arr = QtCore.QByteArray.fromRawData(binary_data)
    img = QtGui.QImage.fromData(arr)
    return QtGui.QPixmap(img)

def import_qt(glbls):
    """ Delayed qt loader. """
    if 'QtCore' in glbls:
        return
        
    from projexui.qt import QtCore, QtGui, wrapVariant, uic
    from projexui.widgets.xloggersplashscreen import XLoggerSplashScreen
    
    glbls['QtCore'] = QtCore
    glbls['QtGui'] = QtGui
    glbls['wrapVariant'] = wrapVariant
    glbls['uic'] = uic
    glbls['XLoggerSplashScreen'] = XLoggerSplashScreen

def findUiActions( widget ):
    """
    Looks up actions for the inputed widget based on naming convention.
    
    :param      widget | <QWidget>
    
    :return     [<QAction>, ..]
    """
    import_qt(globals())
    
    output = []
    for action in widget.findChildren(QtGui.QAction):
        name = nativestring(action.objectName()).lower()
        if ( name.startswith('ui') and name.endswith('act') ):
            output.append(action)
    return output

def formatDropEvent(event):
    """
    Formats information from the drop event.
    
    :param      event | <QtGui.QDropEvent>
    """
    text = []
    
    text.append('#------------------------------------------------------')
    text.append('#                      Drop Data                     ')
    text.append('#------------------------------------------------------')
    
    text.append('\taction: {0}'.format(event.dropAction()))
    text.append('\tmodifiers: {0}'.format(event.keyboardModifiers()))
    text.append('\tbuttons: {0}'.format(event.mouseButtons()))
    text.append('\tpos: {0}'.format(event.pos()))
    text.append('\tpossibleActions: {0}'.format(event.possibleActions()))
    text.append('\tproposedAction: {0}'.format(event.proposedAction()))
    text.append('\tsource: {0}'.format(event.source()))
    
    text.append('#------------------------------------------------------')
    text.append('#                      Mime Data                     ')
    text.append('#------------------------------------------------------')
    
    data = event.mimeData()
    text.append('\tcolorData: {0}'.format(data.colorData()))
    text.append('\thasImage: {0}'.format(data.hasImage()))
    text.append('\thasHtml: {0}'.format(data.hasHtml()))
    text.append('\ttext: {0}'.format(data.text()))
    text.append('\turls: {0}'.format(data.urls()))
    
    text.append('#------------------------------------------------------')
    text.append('#                      Custom Data                     ')
    text.append('#------------------------------------------------------')
    
    for format in data.formats():
        try:
            text.append('\t{0}: {1}'.format(format, data.data(format)))
        except:
            text.append('\t{0}: !!unable to format!!'.format(format))
    
    return '\n'.join(text)

def localizeShortcuts(widget):
    """
    Shifts all action shortcuts for the given widget to us the
    WidgetWithChildrenShortcut context, effectively localizing it to this
    widget.
    
    :param      widget | <QWidget>
    """
    import_qt(globals())
    
    for action in widget.findChildren(QtGui.QAction):
        action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

def loadUi(modulefile, inst, uifile=None, theme='default', className=None):
    """
    Load the ui file based on the module file location and the inputed class.
    
    :param      modulefile  | <str>
                inst        | <subclass of QWidget>
                uifile      | <str> || None
    
    :return     <QWidget>
    """
    if className is None:
        className = inst.__class__.__name__

    import_qt(globals())
    
    currpath = QtCore.QDir.currentPath()
    
    # use compiled information vs. dynamic generation
    widget = None
    if USE_COMPILED:
        # find the root module
        def find_root_module(cls, name):
            if cls.__name__ == name:
                return cls.__module__.rpartition('.')[0]
            else:
                for base in cls.__bases__:
                    if not issubclass(base, QtGui.QWidget):
                        continue

                    out = find_root_module(base, name)
                    if out:
                        return out

        wrapper = QT_WRAPPER.lower()
        root_module = find_root_module(inst.__class__, className)
        if not root_module:
            root_module = inst.__module__.rpartition('.')[0]
        basename = className.lower()
        
        modname_a = '{0}.ui.{1}_{2}_{3}_ui'.format(root_module, basename, theme, wrapper)
        modname_b = '{0}.ui.{1}_{2}_ui'.format(root_module, basename, wrapper)
        modname_c = '{0}.ui.{1}_{2}_ui'.format(root_module, basename, theme)
        modname_d = '{0}.ui.{1}_ui'.format(root_module, basename)
        
        module = None
        for modname in (modname_a, modname_b, modname_c, modname_d):
            modname = modname.strip('.')
            logger.debug('Loading module: {0}...'.format(modname))
            try:
                __import__(modname)
                module = sys.modules[modname]
                break
            except StandardError:
                pass
        
        # successfully loaded a module
        if module:
            # load the module information
            cls = getattr(module, 'Ui_%s' % className, None)
            if not cls:
                for key in module.__dict__.keys():
                    if key.startswith('Ui_'):
                        cls = getattr(module, key)
                        break
            
            # generate the class information
            if cls:
                widget = cls()
                widget.setupUi(inst)
                inst.__dict__.update(widget.__dict__)
    
    if not widget:
        if not uifile:
            uifile = uiFile(modulefile, inst, theme, className=className)
        
        # normalize the path
        uifile = os.path.normpath(uifile)
        if os.path.exists(uifile):
            QtCore.QDir.setCurrent(os.path.dirname(uifile))
            widget = uic.loadUi(uifile, inst)
            QtCore.QDir.setCurrent(currpath)
    
    inst.addActions(findUiActions(inst))
    
    return widget

def exec_( window, data ):
    """
    Executes the startup data for the given main window.  This method needs to 
    be called in conjunction with the setup method.
    
    :sa     setup
    
    :param      window  | <QWidget>
                data    | { <str> key: <variant> value, .. }
    
    :return     <int> err
    """
    import_qt(globals())
    
    if 'splash' in data:
        data['splash'].finish(window)
    
    if not window.parent():
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    
    if 'app' in data:
        # setup application information
        data['app'].setPalette(window.palette())
        data['app'].setWindowIcon(window.windowIcon())
        
        # create the tray menu
        if not window.windowIcon().isNull():
            menu   = QtGui.QMenu(window)
            action = menu.addAction('Quit')
            action.triggered.connect( window.close )
            
            # create the tray icon
            tray_icon = QtGui.QSystemTrayIcon(window)
            tray_icon.setObjectName('trayIcon')
            tray_icon.setIcon(window.windowIcon())
            tray_icon.setContextMenu(menu)
            tray_icon.setToolTip(data['app'].applicationName())
            tray_icon.show()
            window.destroyed.connect(tray_icon.deleteLater)
        
        return data['app'].exec_()
    
    return 0

def setup(applicationName,
          applicationType=None,
          style='plastique',
          splash='',
          splashType=None,
          splashTextColor='white',
          splashTextAlign=None,
          theme=''):
    """
    Wrapper system for the QApplication creation process to handle all proper
    pre-application setup.  This method will verify that there is no application
    running, creating one if necessary.  If no application is created, a None
    value is returned - signaling that there is already an app running.  If you
    need to specify your own QApplication subclass, you can do so through the 
    applicationType parameter.
    
    :note       This method should always be used with the exec_ method to 
                handle the post setup process.
    
    :param      applicationName | <str>
                applicationType | <subclass of QApplication> || None
                style    | <str> || <QStyle> | style to use for the new app
                splash   | <str> | filepath to use for a splash screen
                splashType   | <subclass of QSplashScreen> || None
                splashTextColor   | <str> || <QColor>
                splashTextAlign   | <Qt.Alignment>
    
    :usage      |import projexui
                |
                |def main(argv):
                |   # initialize the application
                |   data = projexui.setup()
                |   
                |   # do some initialization code
                |   window = MyWindow()
                |   window.show()
                |   
                |   # execute the application
                |   projexui.exec_(window, data)
    
    :return     { <str> key: <variant> value, .. }
    """
    import_qt(globals())
    
    output = {}
    
    # check to see if there is a qapplication running
    if not QtGui.QApplication.instance():
        # make sure we have a valid QApplication type
        if applicationType is None:
            applicationType = QtGui.QApplication
        
        app = applicationType([applicationName])
        app.setApplicationName(applicationName)
        app.setQuitOnLastWindowClosed(True)
        
        stylize(app, style=style, theme=theme)
        
        # utilized with the projexui.config.xschemeconfig
        app.setProperty('useScheme', wrapVariant(True))
        output['app'] = app
    
    # create a new splash screen if desired
    if splash:
        if not splashType:
            splashType = XLoggerSplashScreen
        
        pixmap = QtGui.QPixmap(splash)
        screen = splashType(pixmap)
        
        if splashTextAlign is None:
            splashTextAlign = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        
        screen.setTextColor(QtGui.QColor(splashTextColor))
        screen.setTextAlignment(splashTextAlign)
        screen.show()
        
        QtGui.QApplication.instance().processEvents()
        
        output['splash'] = screen
    
    return output

def storePixmap(pixmap, filetype='PNG'):
    import_qt(globals())
    
    arr = QtCore.QByteArray()
    buf = QtCore.QBuffer()
    buf.setBuffer(arr)
    buf.open(QtCore.QBuffer.WriteOnly)
    pixmap.save(buf, filetype)
    buf.close()
    
    return binascii.b2a_base64(nativestring(arr))

def stylize(obj, style='plastique', theme='projexui'):
    """
    Styles the inputed object with the given options.
    
    :param      obj     | <QtGui.QWidget> || <QtGui.QApplication>
                style   | <str>
                base    | <str>
    """
    obj.setStyle(style)
    if theme:
        sheet = resources.read('styles/{0}/style.css'.format(theme))
        if sheet:
            obj.setStyleSheet(sheet)

def topWindow():
    """
    Returns the very top window for all Qt purposes.
    
    :return     <QWidget> || None
    """
    import_qt(globals())
    
    window = QtGui.QApplication.instance().activeWindow()
    if not window:
        return None
    
    parent = window.parent()
    
    while parent:
        window = parent
        parent = window.parent()
        
    return window

def testWidget( widgetType ):
    """
    Creates a new instance for the widget type, settings its properties \
    to be a dialog and parenting it to the base window.
    
    :param      widgetType  | <subclass of QWidget>
    """
    import_qt(globals())
    
    window = QtGui.QApplication.instance().activeWindow()
    widget = widgetType(window)
    widget.setWindowFlags(QtCore.Qt.Dialog)
    widget.show()
    
    return widget

def uiFile(modulefile, inst, theme='', className=None):
    """
    Returns the ui file for the given instance and module file.
    
    :param      moduleFile | <str>
                inst       | <QWidget>
    
    :return     <str>
    """
    if className is None:
        className = inst.__class__.__name__

    # use a module's name vs. filepath
    if modulefile in sys.modules:
        modulefile = sys.modules[modulefile].__file__
    
    clsname  = className.lower()
    basepath = os.path.dirname(nativestring(modulefile))
    
    if theme:
        theme_name = '{0}.{1}.ui'.format(clsname, theme)
        theme_file = os.path.join(basepath, 'ui', theme_name)
        theme_file = re.sub('[\w\.]+\?\d+', '', theme_file)
        
        if os.path.exists(theme_file):
            return theme_file
    
    base_name = '{0}.ui'.format(clsname)
    base_file = os.path.join(basepath, 'ui', base_name)
    base_file = re.sub('[\w\.]+\?\d+', '', base_file)
    
    return base_file