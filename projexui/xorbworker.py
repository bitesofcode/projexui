#!/usr/bin/python

""" Creates a threadable worker object for looking up ORB records. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import threading
from xqt import QtCore

try:
    from orb.errors import Interruption, ConnectionLostError
except ImportError:
    class Interruption(Exception):
        pass
    class ConnectionLostError(Exception):
        pass

class XOrbWorkerThreadManager(object):
    _thread = None
    
    @staticmethod
    def destroy():
        thread = XOrbWorkerThreadManager._thread
        if thread is None:
            return
        
        XOrbWorkerThreadManager._thread = None
        
        thread.quit()
        thread.wait()
    
    @staticmethod
    def thread():
        if not XOrbWorkerThreadManager._thread:
            thread = QtCore.QThread()
            thread.start()
            
            app = QtCore.QCoreApplication.instance()
            app.aboutToQuit.connect(XOrbWorkerThreadManager.destroy)
            
            XOrbWorkerThreadManager._thread = thread
        
        return XOrbWorkerThreadManager._thread

#----------------------------------------------------------------------

class XOrbWorker(QtCore.QObject):
    loadingStarted = QtCore.Signal()
    loadingFinished = QtCore.Signal()
    connectionLost = QtCore.Signal()
    
    WorkerCount = 0
    
    def __init__(self, threaded, *args):
        super(XOrbWorker, self).__init__(*args)
        
        # define custom properties
        self._database = None
        self._loading = False
        self._databaseThreadId = 0
        
        XOrbWorker.WorkerCount += 1
        
        if threaded:
            self.moveToThread(XOrbWorkerThreadManager.thread())
    
    def __del__(self):
        XOrbWorker.WorkerCount -= 1
        if XOrbWorker.WorkerCount == 0:
            XOrbWorkerThreadManager.destroy()
    
    def database(self):
        """
        Returns the database associated with this worker.
        
        :return     <orb.Database>
        """
        return self._database
    
    def databaseThreadId(self):
        """
        Returns the thread id associated with this worker.
        
        :return     <int>
        """
        return self._threadId
    
    def deleteLater(self):
        """
        Prepares to delete this worker.  If a database and a particular
        thread id are associated with this worker, then it will be cleared
        when it is deleted.
        """
        self.interrupt()
        super(XOrbWorker, self).deleteLater()
    
    def finishLoading(self):
        """
        Marks the worker as having completed loading.
        """
        self._loading = False
        self.loadingFinished.emit()
    
    def isLoading(self):
        """
        Returns whether or not this worker is currently loading.
        
        :return     <bool>
        """
        return self._loading
    
    def interrupt(self):
        """
        Interrupts the current database from processing.
        """
        if self._database and self._databaseThreadId:
            # support Orb 2 interruption capabilities
            try:
                self._database.interrupt(self._databaseThreadId)
            except AttributeError:
                pass
        
        self._database = None
        self._databaseThreadId = 0
    
    def setDatabase(self, database):
        """
        Sets the database associated with this thread to the inputed database.
        
        :param      database | <orb.Database>
        """
        self._database = database
        if self.thread():
            tid = threading.current_thread().ident
            self._databaseThreadId = tid
    
    def startLoading(self):
        """
        Marks the workar as having started loading.
        """
        self._loading = True
        self.loadingStarted.emit()
    
    def waitUntilFinished(self):
        """
        Processes the main thread until the loading process has finished.  This
        is a way to force the main thread to be synchronous in its execution.
        """
        QtCore.QCoreApplication.processEvents()
        while self.isLoading():
            QtCore.QCoreApplication.processEvents()
    
    @staticmethod
    def interruptionProtected(func):
        def wraps(*args, **kwds):
            try:
                func(*args, **kwds)
            except Interruption:
                pass
        return wraps