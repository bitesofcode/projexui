#!/usr/bin/python

""" Defines the ruler class to control what the scale for the cart is. """

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

import logging

from projex.text import nativestring

from projexui.qt.QtCore import Qt,\
                               QDate,\
                               QDateTime,\
                               QTime

from projexui.qt.QtGui import QApplication,\
                              QFontMetrics

from projex.enum import enum

logger = logging.getLogger(__name__)

class XChartRuler(object):
    Type = enum('Number', 
                'Date', 
                'Datetime', 
                'Time', 
                'Monthly',
                'Custom')
    
    def __init__( self, rulerType ):
        
        # define custom properties
        self._rulerType     = rulerType
        self._minimum       = None
        self._maximum       = None
        self._step          = None
        self._notches       = None
        self._format        = None
        self._title         = ''
        self._padStart      = 0
        self._padEnd        = 0
        self._notchPadding  = 6
        
        self.setRulerType(rulerType)
    
    def calcTotal( self, values ):
        """
        Calculates the total for the given values.  For Datetime/Time objects,
        this will be seconds from minimum to maximum - defaulting to 1 second.
        For Date objects, this will be days from minimum to maximum, defaulting
        to 1 day.  For Number objects, this will be the sum of the list.  For
        Custom objects, a -1 value is returned.
        
        :param      values | [<variant>, ..]
        
        :return     <int>
        """
        rtype = self.rulerType()
        
        if ( not values ):
            return 0
        
        if ( rtype == XChartRuler.Type.Number ):
            return sum(values)
        
        elif ( rtype == XChartRuler.Type.Date ):
            values.sort()
            days = values[0].daysTo(values[-1])
            return max(1, days)
        
        elif ( rtype in (XChartRuler.Type.Datetime, XChartRuler.Type.Time) ):
            values.sort()
            secs = values[0].secsTo(values[-1])
            return max(1, secs)
        
        return -1
    
    def clear( self ):
        """
        Clears all the cached information about this ruler.
        """
        self._minimum   = None
        self._maximum   = None
        self._step      = None
        self._notches   = None
        self._format    = None
        self._formatter = None
        self._padEnd    = 0
        self._padStart  = 0
    
    def compareValues( self, a, b ):
        """
        Compares two values based on the notches and values for this ruler.
        
        :param      a | <variant>
                    b | <variant>
        
        :return     <int> 1 || 0 || -1
        """
        if ( self.rulerType() in (XChartRuler.Type.Custom, 
                                  XChartRuler.Type.Monthly) ):
            
            try:
                aidx = self._notches.index(a)
            except ValueError:
                return -1
            
            try:
                bidx = self._notches.index(b)
            except ValueError:
                return 1
            
            return cmp(aidx, bidx)
        
        return cmp(a, b)
    
    def format( self ):
        """
        Returns the format that will be used for this ruler.
        
        :return     <str>
        """
        if ( self._format is not None ):
            return self._format
        
        rtype = self.rulerType()
        if ( rtype == XChartRuler.Type.Number ):
            self._format = '%i'
        
        elif ( rtype == XChartRuler.Type.Date ):
            self._format = 'M.d.yy'
        
        elif ( rtype == XChartRuler.Type.Datetime ):
            self._format = 'M.d.yy @ h:mm ap'
        
        elif ( rtype == XChartRuler.Type.Time ):
            self._format = 'h:mm ap'
        
        return self._format
    
    def formatter( self ):
        """
        Returns the formatter callable that is linked with this ruler for 
        formatting the value for a notch to a string.
        
        :return     <callable>
        """
        return self._formatter
    
    def formatValue( self, value ):
        """
        Formats the inputed value based on the formatting system for this ruler.
        
        :param      value | <variant>
        """
        formatter = self.formatter()
        if ( formatter is not None ):
            return formatter(value)
        
        elif ( self.format() ):
            rtype = self.rulerType()
            if ( rtype in (XChartRuler.Type.Date, XChartRuler.Type.Datetime,
                           XChartRuler.Type.Time) ):
                return value.toString(self.format())
            else:
                try:
                    return self.format() % value
                except TypeError:
                    return nativestring(value)
        
        return nativestring(value)
    
    def maxNotchSize( self, orientation ):
        """
        Returns the maximum size for this ruler based on its notches and the
        given orientation.
        
        :param      orientation | <Qt.Orientation>
        
        :return     <int>
        """
        metrics = QFontMetrics(QApplication.font())
        
        if orientation == Qt.Vertical:
            notch = ''
            for n in self.notches():
                if len(nativestring(n)) > len(nativestring(notch)):
                    notch = nativestring(n)
            
            return metrics.width(notch)
        else:
            return metrics.height()
    
    def minLength( self, orientation ):
        """
        Returns the minimum length for this ruler based on its notches and the
        given orientation.
        
        :param      orientation | <Qt.Orientation>
        
        :return     <int>
        """
        padding         = self.padStart() + self.padEnd()
        count           = len(self.notches())
        notch_padding   = self.notchPadding()
        
        if ( orientation == Qt.Horizontal ):
            section     = self.maxNotchSize(Qt.Vertical)
        else:
            section     = self.maxNotchSize(Qt.Horizontal)
        
        return notch_padding * count + section * count + padding
    
    def maximum( self ):
        """
        Returns the maximum value for this ruler.  If the cached value is None,
        then a default value will be specified based on the ruler type.
        
        :return     <variant>
        """
        if ( self._maximum is not None ):
            return self._maximum
        
        rtype = self.rulerType()
        
        if ( rtype == XChartRuler.Type.Number ):
            self._maximum = 100
            
        elif ( rtype == XChartRuler.Type.Date ):
            self._maximum = QDate.currentDate().addDays(10)
        
        elif ( rtype == XChartRuler.Type.Datetime ):
            self._maximum = QDateTime.currentDateTime().addDays(10)
        
        elif ( rtype == XChartRuler.Type.Time ):
            self._maximum = QDateTime.currentDateTime().time().addSecs(60 * 60)
            
        else:
            notches = self.notches()
            if ( notches ):
                self._maximum = notches[-1]
                
        return self._maximum
    
    def minimum( self ):
        """
        Returns the minimum value for this ruler.  If the cached value is None,
        then a default value will be specified based on the ruler type.
        
        :return     <variant>
        """
        if ( self._minimum is not None ):
            return self._minimum
        
        rtype = self.rulerType()
        
        if ( rtype == XChartRuler.Type.Number ):
            self._minimum = 0
            
        elif ( rtype == XChartRuler.Type.Date ):
            self._minimum = QDate.currentDate()
        
        elif ( rtype == XChartRuler.Type.Datetime ):
            self._minimum = QDateTime.currentDateTime()
        
        elif ( rtype == XChartRuler.Type.Time ):
            self._minimum = QDateTime.currentDateTime().time()
        
        else:
            notches = self.notches()
            if ( notches ):
                self._minimum = notches[0]
        
        return self._minimum
    
    def notches( self ):
        """
        Reutrns a list of the notches that are going to be used for this ruler.
        If the notches have not been explicitly set (per a Custom type), then
        the notches will be generated based on the minimum, maximum and step
        values the current ruler type.
        
        :return     [<str>, ..]
        """
        if ( self._notches is not None ):
            return self._notches
        
        rtype           = self.rulerType()
        formatter       = self.formatter()
        format          = self.format()
        self._notches   = []
        
        minimum = self.minimum()
        maximum = self.maximum()
        step    = self.step()
        
        if ( step <= 0 ):
            return []
        
        curr = minimum
        while ( curr < maximum ):
            self._notches.append(self.formatValue(curr))
            
            if ( rtype == XChartRuler.Type.Number ):
                curr += step
            elif ( rtype == XChartRuler.Type.Date ):
                curr = curr.addDays(step)
            elif ( rtype in (XChartRuler.Type.Datetime, XChartRuler.Type.Time)):
                curr = curr.addSecs(step)
            else:
                break
        
        self._notches.append(self.formatValue(maximum))
        
        return self._notches
    
    def notchPadding( self ):
        """
        Returns the minimum padding amount used between notches.
        
        :return     <int>
        """
        return self._notchPadding
    
    def padEnd( self ):
        """
        Returns the number of units to use as padding for the end of this ruler.
        
        :return     <int>
        """
        return self._padEnd
    
    def padStart( self ):
        """
        Returns the number of units to use as padding for the beginning of
        this ruler.
        
        :return     <int>
        """
        return self._padStart
    
    def percentAt( self, value ):
        """
        Returns the percentage where the given value lies between this rulers
        minimum and maximum values.  If the value equals the minimum, then the
        percent is 0, if it equals the maximum, then the percent is 1 - any
        value between will be a floating point.  If the ruler is a custom type,
        then only if the value matches a notch will be successful.
        
        :param      value | <variant>
        
        :return     <float>
        """
        if ( value is None ):
            return 0.0
        
        minim = self.minimum()
        maxim = self.maximum()
        rtype = self.rulerType()
        
        # simple minimum
        if ( value == minim and not self.padStart() ):
            perc = 0.0
        
        # simple maximum
        elif ( value == maxim and not self.padEnd() ):
            perc = 1.0
        
        # calculate a numeric percentage value
        elif ( rtype == XChartRuler.Type.Number ):
            perc  = float(value - minim) / float(maxim - minim)
        
        # calculate a time percentage value
        elif ( rtype in (XChartRuler.Type.Datetime, XChartRuler.Type.Time) ):
            maxsecs = minim.secsTo(maxim)
            valsecs = minim.secsTo(value)
            
            perc    = float(valsecs) / maxsecs
        
        # calculate a date percentage value
        elif ( rtype == XChartRuler.Type.Date ):
            maxdays = minim.daysTo(maxim)
            valdays = minim.daysTo(value)
            
            perc    = float(valdays) / maxdays
        
        # otherwise, compare against the notches
        else:
            perc    = 0.0
            notches = self.notches()
            count   = len(notches)
            count  += self.padStart() + self.padEnd()
            count   = max(1, count - 1)
            
            perc    = float(self.padStart()) / count
            
            for i, notch in enumerate(notches):
                if ( notch == value ):
                    perc += float(i) / count
                    break
        
        # normalize the percentage
        perc    = min(perc, 1.0)
        perc    = max(0, perc)
        
        return perc
    
    def rulerType( self ):
        """
        Returns the ruler type for this ruler.
        
        :reutrn     <XChartRuler.Type>
        """
        return self._rulerType
    
    def setFormat( self, format ):
        """
        Sets the string format that will be used when processing the ruler
        notches.  For a Number type, this will be used as a standard string
        format in Python (%i, $%0.02f, etc.).  For Datetime, Date, and Time
        types, it will be used with the QDate/QDateTime/QTime toString method.
        
        For Custom types, notches should be set manually.
        """
        self._format = format
        
    def setFormatter( self, formatter ):
        """
        Sets the formatter method or callable that will accept one of the values
        for this ruler to render out the text display for the value.
        
        :param      formatter | <callable>
        """
        self._formatter = formatter
        
    def setMaximum( self, maximum ):
        """
        Sets the maximum value for this ruler to the inputed value.
        
        :param      maximum | <variant>
        """
        self._maximum = maximum
        self._notches = None
    
    def setMinimum( self, minimum ):
        """
        Sets the minimum value for this ruler to the inputed value.
        
        :param      minimum | <variant>
        """
        self._minimum = minimum
        self._notches = None
    
    def setNotches( self, notches ):
        """
        Manually sets the notches list for this ruler to the inputed notches.
        
        :param      notches | [<str>, ..] || None
        """
        self._rulerType = XChartRuler.Type.Custom
        self._notches = notches
    
    def setNotchPadding( self, padding ):
        """
        Sets the minimum padding amount used between notches.
        
        :param      padding | <int>
        """
        self._notchPadding = padding
    
    def setPadEnd( self, amount ):
        """
        Sets the number of units to use as padding for the end of this ruler.
        
        :param      amount | <int>
        """
        self._padEnd = amount
    
    def setPadStart( self, amount ):
        """
        Sets the number of units to use as padding for the beginning of
        this ruler.
        
        :param      amount | <int>
        """
        self._padStart = amount
    
    def setRulerType( self, rulerType ):
        """
        Sets the ruler type for this ruler to the inputed type.
        
        :param      rulerType | <XChartRuler.Type>
        """
        self._rulerType = rulerType
        self.clear()
        
        # handle custom types
        if ( rulerType == XChartRuler.Type.Monthly ):
            self.setNotches(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    
    def setStep( self, step ):
        """
        Sets the step value for this ruler to the inputed value.  If the ruler
        type is Number, then an int or float value is acceptable.  If the type
        is Datetime or Date, then the step value is an integer representing
        days.  If the type is Time, then the step is an integer representing 
        seconds.
        
        :param      step | <int> || <float>
        """
        self._step    = int(step)
        self._notches = None
    
    def setTitle( self, title ):
        """
        Sets the title for this ruler to the inputed title.
        
        :param      title | <str>
        """
        self._title = title
    
    def step( self ):
        """
        Returns the step value for this ruler.  If the cached value is None,
        then a default value will be specified based on the ruler type.
        
        :return     <variant>
        """
        if ( self._step is not None ):
            return self._step
        
        elif ( self.rulerType() == XChartRuler.Type.Number ):
            self._step = int((self.maximum() - self.minimum()) / 10.0)
        
        elif ( self.rulerType() == XChartRuler.Type.Date ):
            
            self._step = int(self.minimum().daysTo(self.maximum()) / 10.0) - 1
        
        elif ( self.rulerType() & (XChartRuler.Type.Time | \
                                   XChartRuler.Type.Datetime) ):
            self._step = int(self.minimum().secsTo(self.maximum()) / 10.0) - 1
        
        return self._step
    
    def title( self ):
        """
        Returns the title for this ruler.
        
        :return     <str>
        """
        return self._title
    
    def valueAt( self, percent ):
        """
        Returns the value at the inputed percent.
        
        :param     percent | <float>
        
        :return     <variant>
        """
        minim = self.minimum()
        maxim = self.maximum()
        rtype = self.rulerType()
        
        # simple minimum
        if ( percent <= 0 ):
            return minim
        
        # simple maximum
        elif ( 1 <= percent ):
            return maxim
        
        # calculate a numeric percentage value
        elif ( rtype == XChartRuler.Type.Number ):
            return (maxim - minim) * percent
        
        # calculate a time percentage value
        elif ( rtype in (XChartRuler.Type.Datetime, XChartRuler.Type.Time) ):
            maxsecs = minim.secsTo(maxim)
            
            diff = maxssecs * percent
            return minim.addSecs(diff)
            
        # calculate a date percentage value
        elif ( rtype == XChartRuler.Type.Date ):
            maxdays = minim.daysTo(maxim)
            
            diff = maxdays * percent
            return minim.addDays(diff)
            
        # otherwise, compare against the notches
        else:
            perc    = 0.0
            notches = self.notches()
            count   = len(notches)
            count  += self.padStart() + self.padEnd()
            count   = max(1, count - 1)
            
            perc    = float(self.padStart()) / count
            last    = None
            
            for i, notch in enumerate(notches):
                perc += float(i) / count
                if ( perc <= percent ):
                    break
                
                last = notch
            
            return last