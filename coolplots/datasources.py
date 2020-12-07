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
from contextlib import contextmanager

import numpy as np
import numpy
import numpy.ctypeslib
import ctypes
import warnings
import gc
import multiprocessing
import multiprocessing.sharedctypes
import math
import random
import h2pyex


try:
    from .support import *
    from .datagenerators import *
except ValueError:
    from support import *
    from datagenerators import *



#from pyqtgraph.multiprocess.remoteproxy import ObjectProxy
_logger = utils.get_logger(__name__)




class SampleDataSource(object):
    def __init__(self, pps=1000, delay=0.2):
        super(SampleDataSource, self).__init__()
        print("Created SampleDataSource at %d pps"%pps)
        self.sample_period = 1.0/pps
        self.timestamp = time.time()+delay
        self.test_src = TestDataGenerator(10)
        self.rand_src = RandomDataGenerator(10)
        self.env = {}
        self.env['test'] = self.test_src.getData()
        self.env['rand'] = self.rand_src.getData()
    
    
    def getSamples(self):
        if time.time() > self.timestamp:
            self.test_src.getData()
            self.rand_src.getData()
            self.timestamp += self.sample_period
            return self.env
        else:
            return None
    
    def initialSamples(self):
        """
        Get the intitial sample the data structure before it is evaluated so that
        the type and structure can be determined.
        """
        return self.env
    
    def close(self):
        """
        Close the data source
        """
        print("Closing SampleDataSource...")


if __name__ == '__main__':
    import h2pyex
    from ctypes import *
    
    from io import StringIO
    hfile = """
    typedef struct mystream_tag {
        int32_t x;
        float32_t y;
        int32_t z;
    } POINT;
    """
    
    streammod = h2pyex.import_cheader(hfile, "streammod", packing=None)
    DataReader(streammod.POINT, 20)

