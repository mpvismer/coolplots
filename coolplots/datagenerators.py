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
except ValueError:
    from support import *



#from pyqtgraph.multiprocess.remoteproxy import ObjectProxy
_logger = utils.get_logger(__name__)


class DataGenerator(object):
    
    def __init__(self):
        super(DataGenerator, self).__init__()
    
    
    def updateData(self):
        raise Exception("Not implemented.")
    
    def getData(self):
        """
        Returns an instance of data
        """
        self.updateData(self._store)
        return self._store
    
    
    def getDataArray(self):
        """
        Returns an array of data.
        """
        for data in self._storeArray:
            self.updateData(data)
        return self._storeArray
    
    
    def exampleData(self):
        """
        Returns a sample of the data - used to determine GUI layout etc.
        """
        return self._dataType()


class TestDataGenerator(DataGenerator):
    def __init__(self, buflen=10):
        super(TestDataGenerator, self).__init__()
        class TestStream:
            count = 0
            b_float = 0.3;
            b_float2 = 0.0
            b_int = 4
            b_str = 'hello'
            b_1dint = [3]*12
            b_2dint = [[3,2],[3,1],[4,1]]
            b_1dstr = ['sdf', 'great', 'works']
        self._buflen = buflen
        self._dataType = TestStream
        self._store = self._dataType()
        self._storeArray = [self._dataType() for idx in range(self._buflen)]
        self._count = 0
    
    
    def updateData(self, obj):
        self._count += 1
        obj.count = self._count
        obj.b_float = math.sin(2*math.pi/(100*self._buflen)*self._count)*100
        obj.b_float2 = self._count/self._buflen % 100
        obj.b_int = int(np.sign(obj.b_float))*100
        return obj


class RandomDataGenerator(DataGenerator):
    
    def __init__(self, buflen=10):
        super(RandomDataGenerator, self).__init__()
        streammod = h2pyex.import_cheader("""
            struct mystream_tag {
             int64_t count;
             float a_float;
             float a_float2;
             int32_t a_int;
             //char a_str[10];
             int32_t a_1dint[12];
             //int32_t a_2dint[3][2];
             //char a_1dstr[3][6];
            };
        """, "streammod")
        self._dataType = getattr(streammod, 'mystream_tag')
        self._buflen = buflen
        self._store = self._dataType()
        self._storeArray = (self._dataType*self._buflen)()
        self._count = 0
    
    
    def updateData(self, obj):
        self._count += 1
        obj.count = self._count
        obj.a_float = math.sin(2*math.pi/(70*self._buflen)*self._count)*50 + random.randint(-50,50)
        obj.a_float2 = int(math.sin(2*math.pi/(60*self._buflen)*self._count)*random.randint(-100,100))
        obj.a_int = random.randint(-20,20) + random.randint(-20,20) + random.randint(-20,20)
        return obj
    
    
    def getDataType(self):
        return self._dataType*self._buflen



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

