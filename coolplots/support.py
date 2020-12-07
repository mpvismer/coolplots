"""
Original work Copyright (c) 2015 Mark Vismer
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import weakref
import time
import numpy as np

try:
    import utils
except ImportError:
    path = os.path.realpath(os.path.abspath(os.path.join(__file__,'../../../Python')))
    sys.path.append(path)
    import utils

#import PySide

path = os.path.realpath(os.path.abspath(os.path.join(__file__,'../../../../../pyqtgraph')))
sys.path.insert(0, path)

pyqtgraph = utils.install_import('pyqtgraph')

from pyqtgraph.Qt import QtCore, QtGui, uic


import pyqtgraph as pg
from pyqtgraph.dockarea import *

_logger = utils.get_logger(__name__)

#pg.setConfigOptions(useOpenGL=True)
pg.setConfigOptions(antialias=True)  ## prettier plots at no cost to the main process!


def notify_destroy(x):
    temps = str(x)
    def printit(dummy):
        _logger.info("%s was destroyed." % temps)
    if not hasattr(sys,'myrefs'):
        sys.myrefs = []
    sys.myrefs.append(weakref.ref(x, printit))



