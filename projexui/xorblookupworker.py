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

import logging
import time

from projexui.qt import Signal, SIGNAL, wrapNone
from projexui.xorbworker import XOrbWorker, Interruption, ConnectionLostError

try:
    from orb import Orb, RecordSet, Table, RecordCache, errors
except ImportError:
    Orb = None
    Table = None
    RecordCache = None
    RecordSet = None
    errors = None

logger = logging.getLogger(__name__)

class XOrbLookupWorker(XOrbWorker):
    columnLoaded = Signal(object, object, object)
    loadedGroup = Signal(object, object, list)
    loadedRecords = Signal((object,), (object, object))
    
    def __init__(self, *args):
        super(XOrbLookupWorker, self).__init__(*args)
        
        # define custom properties
        self._cancelled = False
        self._running   = False
        self._batchSize = 100
        self._batched   = True
        self._preloadColumns = []
    
    def batchSize(self):
        """
        Returns the page size for this loader.
        
        :return     <int>
        """
        return self._batchSize
    
    def cancel(self):
        """
        Cancels the current lookup.
        """
        if self._running:
            self.interrupt()
            self._running = False
            self._cancelled = True
            self.loadingFinished.emit()
    
    def isBatched(self):
        """
        Returns whether or not this worker is processing in batches.  You should
        enable this if you are not working with paged results, and disable
        if you are working with paged results.
        
        :return     <bool>
        """
        return self._batched
    
    def isRunning(self):
        """
        Returns whether or not this worker is currently running.
        """
        return self._running
    
    def loadColumns(self, records, columnName):
        """
        Loads the column information per record for the given records.
        
        :param      records     | [<orb.Table>, ..]
                    columnName  | <str>
        """
        try:
            for record in records:
                col = record.schema().column(columnName)
                if not col:
                    continue
                
                value = record.recordValue(col.name(), autoInflate=True)
                self.columnLoaded.emit(record, col.name(), wrapNone(value))
        
        except ConnectionLostError:
            self.connectionLost.emit()
        
        except Interruption:
            pass
    
    def loadBatch(self, records):
        """
        Loads the records for this instance in a batched mode.
        """
        try:
            curr_batch = records[:self.batchSize()]
            next_batch = records[self.batchSize():]
            
            curr_records = list(curr_batch)
            if self._preloadColumns:
                for record in curr_records:
                    record.recordValues(self._preloadColumns)
            
            if len(curr_records) == self.batchSize():
                self.loadedRecords[object, object].emit(curr_records,
                                                        next_batch)
            else:
                self.loadedRecords[object].emit(curr_records)
        
        except ConnectionLostError:
            self.connectionLost.emit()
        
        except Interruption:
            pass
    
    def loadRecords(self, records):
        """
        Loads the record set for this instance.
        
        :param      records | <orb.RecordSet> || <list>
        """
        try:
            if self._running:
                return
            
            self._cancelled = False
            self._running = True
            
            try:
                self.setDatabase(records.database())
            except AttributeError:
                pass
            
            self.startLoading()
            
            # make sure the orb module is loaded, or there is really no point
            if RecordSet is None:
                logger.error('Orb was not loaded.')
            
            # lookup a group of results
            if RecordSet.typecheck(records) and records.groupBy():
                levels = records.groupBy()
                next_levels = levels[1:]
                
                for key, records in records.grouped(levels[0]).items():
                    if self._cancelled:
                        break
                    
                    # PySide Hack! Emitting None across threads will crash Qt
                    #              when in PySide mode.
                    if key == None:
                        key = 'None'
                    
                    self.loadedGroup.emit(key, records, next_levels)
            
            # lookup a list of results, in batched mode
            elif self.isBatched():
                self.loadBatch(records)
                
            # lookup a list of results, not in batched mode
            else:
                records = list(records)
                if self._preloadColumns:
                    for record in curr_records:
                        record.recordValues(self._preloadColumns)
                
                self.loadedRecords[object].emit(records)
            
            self._running = False
            self.finishLoading()
        except ConnectionLostError:
            self.finishLoading()
            self.connectionLost.emit()
        except Interruption:
            self.finishLoading()
        finally:
            self.finishLoading()

    def preloadColumns(self):
        """
        Sets the list of pre-load columns for this worker.
        
        :return     [<str>, ..]
        """
        return self._preloadColumns
    
    def setBatchSize(self, batchSize):
        """
        Sets the page size for this loader.
        
        :param     batchSize | <int>
        """
        self._batchSize = batchSize
    
    def setBatched(self, state):
        """
        Sets the maximum number of records to extract.  This is used in
        conjunction with paging.
        
        :param      maximum | <int>
        """
        self._batched = state
    
    def setPreloadColumns(self, columns):
        """
        Sets the list of pre-load columns for this worker.
        
        :param      columns | [<str>, ..]
        """
        self._preloadColumns = columns[:]


