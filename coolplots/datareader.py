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
except:
    from support import *



#from pyqtgraph.multiprocess.remoteproxy import ObjectProxy

_logger = utils.get_logger(__name__)




def makeDataObject(num):
    """
    Creates the ctypes data object used by both processes - defines the layout
    of the shared memory.
    """
    class DataBlock(ctypes.Structure):
            _fields_ = [("y", ctypes.c_float*(num*3)),
                        ("y10", ctypes.c_float*(num//10*3)),
                        ("y100", ctypes.c_float*(num//100*3)),
                        ("endpoint", ctypes.c_ssize_t),
                        ("startpoint", ctypes.c_ssize_t),
                        ("pltcurrent", ctypes.c_ssize_t)]
    return num






class SlavedDataPacker(object):
    """
    This class manages an object which handles packign data in for the received
    class.
    """
    def __init__(self, memkey, numpoints, expr):
        self.shared = QtCore.QSharedMemory()
        self.shared.attach(QtCore.QSharedMemory.ReadWrite)
        self.



def target(child_conn, *args):
    mems = []
    while 1:
        res = child_conn.get(block=False)
        if res is dict:
            shared = QtCore.QSharedMemory()
            mem = shared.attach(QtCore.QSharedMemory.ReadWrite)
            
            mems.append((res['y_expr'], mem))
        
        
        for expr, mem in mems:
            try:
                val = eval(expr, globals(), datas)
            except:
                #ignore these no data
                #traceback.print_exc()
                #self.removeCurve(key)
                pass
            else:
                #while len(plotdata) >= self.streamBufferLen:
                #    plotdata.remove(plotdata[0])
                #plotdata.append(val)
                #curve.setData(range(self.streamBufferLen-len(plotdata), self.streamBufferLen), plotdata) #, _callSync='off')
                if mem.endpoint >
                mem.y[mem.endpoint] = mem.y
                mem.endpoint++
        
        arg in args:
        if arg.num



class RemoteDataSource(object):
    """
    Handles reading data
    """
    
    
    def __init__(self, clsInstance):
        super(DataReader, self).__init__()
        self.con, child_conn = Pipe()
        p = Process(target=f, args=(child_conn,))
        p.start()
        
        #self._readerProc = multiprocess.Process(targert=reader_worker, args = (,))
        
        #self.locks = [multiprocessing.Lock(), multiprocessing.Lock()]
        #self.sharedMem = tuple( multiprocessing.sharedctypes.Value(SharedData, lock) for lock in self.locks)
        #self.sharedMem = tuple( multiprocessing.sharedctypes.RawValue(SharedData) for lock in self.locks)
        for shared in self.sharedMem:
            shared.num = 0;
        
        
        class SharedData(Structure):
            _fields_ = [("num", c_size_t),
                        ("data", cls.getDataType())]
    
    
    
    def addPlot(self, param):
        self.con.send(param)
        
        #self.structArrays = [ np.array(mem, copy=False) for mem in self.sharedMem ]
        #self.recArrays = [ sa.view(np.recarray) for sa in self.structArrays ]
        #print(self.recArrays[0].x)
    
    
    @contextmanager
    def getData(self):
        self._toRelease = None
        for shared in self.sharedMem:
            #if shared.get_lock().aquire(block=False):
            #    self._toRelease = shared.get_lock()
            obj = shared
            if obj.num > 0:
                yield shared.data[:obj.num]
                obj.num = 0
                break




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

