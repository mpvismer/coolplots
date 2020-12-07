"""
Original work Copyright (c) 2015 Mark Vismer

Defines the interface for a DataSource class which provides the data for a
plotter.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import weakref
import traceback
import time
import types
import collections

import numpy as np

try:
    from .support import *
    from .datasources import *
except:
    from support import *
    from datasources import *

_logger = utils.get_logger(__name__)



class CurveData(object):
    def __init__(self, expr='', numpoints=5000, sourceName=None):
        super(CurveData, self).__init__()
        self._numpoints = numpoints
        self.sourceName = sourceName
        self.error = None
        self.setExpr(expr)
        self._d = []
    
    
    def clearError(self):
        """
        Clear the error for this CurveDatta
        """
        self.error = None
        self.setExpr(self._expr)
    
    
    def setExpr(self, expr):
        self.error = None
        self._expr = expr
    
    
    def getExpr(self):
        return self._expr
    
    
    def clearData(self):
        self._d = []
    
    
    def getData(self):
        return np.array(self._d)
    
    
    def addPoint(self, val):
        self._d.append(val)
        if len(self._d) >= self._numpoints:
            del self._d[0]
    
    def evalPoint(self, sample):
        return eval(self._expr, globals(), sample)

