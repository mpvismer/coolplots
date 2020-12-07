"""
Original work Copyright (c) 2015 Mark Vismer
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import collections
import inspect
import traceback
from functools import partial
import numpy as np
import gc
import weakref
import ctypes
import logging
import numpy as np


try:
    from .support import *
except:
    from support import *


CURVES = weakref.WeakValueDictionary()


class CpCurve(object):
    """
    Saves an instance of a curve and its properties.
    """
    
    name = None
    x_expr = None
    #x_compiled = None
    y_expr = None
    #y_compiled = None
    penColour = None
    penWidth = 1
    
    def __init__(self, **kwargs):
        """
        Constructor
        """
        super(CpCurve, self).__init__()
        self.setSettings(**kwargs)
    
    
    def getSettings(self):
        return dict(utils.enum_fields(self))
    
    
    def setSettings(self, settings=None, **kwargs):
        if settings is None:
            settings = kwargs
        for (key, val) in kwargs.items():
            setattr(self, key, val)
        self.name = self.name or self.y_expr
        self.y_expr = self.y_expr or self.name
        CURVES[id(self)] = self
    
    def getOpts(self):
        d = {}
        d['pen'] = pg.mkPen(color=self.penColour, width=self.penWidth)
        return d


if __name__ == '__main__':
    filename, file_extension = os.path.splitext(__file__)
    utils.configure_rotating_logging(
        filename+'.log',
        level=getattr(logging, "DEBUG"), maxBytes=128*1024)
    
    if QtGui.QApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
    
    c = CurveItem()
