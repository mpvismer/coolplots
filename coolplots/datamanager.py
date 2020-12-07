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


class DataManager(object):
    """
    A class/interface for providing curve data source to plot.
    """
    def __init__(self,  curveCls, numpoints=10000, **kwargs):
        super(DataManager, self).__init__()
        self._numpoints = numpoints
        self._lostCurveDatas = weakref.WeakSet()
        self._curveCls = curveCls
        self._lastSamples = collections.OrderedDict()
        self._sources = collections.OrderedDict()
    
    
    def addDataSource(self, source=SampleDataSource, name='default', sourceModule=None, sourceArgs=[], sourceKwargs={}):
        if name in self._sources:
            raise Exception('Data source "%s" already exists!' % name)
        if utils.isstr(source):
            if utils.isstr(sourceModule):
                sourceModule = __import__(sourceModule)
            if sourceModule is not None:
                source = sourceModule.__dict__[source]
        elif type(source) in [ types.ClassType, types.TypeType]:
            source = source(*sourceArgs, **sourceKwargs)
        cds = weakref.WeakSet()
        self._sources[name] = (source, cds)
        self._lastSamples[name] = source.initialSamples()
        for cd in list(self._lostCurveDatas):
            if self._tryAddToDataSource(cd, name):
                  self._lostCurveDatas.remote(cds)
    
    
    def _tryAddToDataSource(self, curveData, sourceName):
        """
        Tries to add the CurveData for the DataSource name.
        """
        try:
            curveData.evalPoint(self._lastSamples[sourceName])
        except Exception as e:
            curveData.error = e
        else:
            curveData.sourceName = sourceName
            curveData.clearError()
            self._sources[sourceName][1].add(curveData)
            _logger.info('Adding CurveData to data source names "%s"' % sourceName)
        return curveData.error is None
    
    
    def createCurveData(self, **kwargs):
        """
        Returns a sample of the data - used to determine MENUs etc for adding
        plots
        """
        kwargs['numpoints'] = kwargs.get('numpoints', self._numpoints)
        cd = self._curveCls(**kwargs)
        if cd.error:
            return cd
        if cd.sourceName:
            source, cds = self._sources.items[cd.sourceName]
            cds.add(cd)
        else:
            for name in self._sources:
                if self._tryAddToDataSource(cd, name):
                    return cd
            self._lostCurveDatas.add(cd)
        return cd
    
    
    def updateCurveData(self, timeout=0.1):
        """
        Update all the curve data.
        """
        start = time.time()
        for key, (source, curvedatas) in self._sources.items():
            while time.time() - start < timeout:
                env = source.getSamples()
                if env is not None:
                    self._lastSamples[key] = env
                    for cd in curvedatas:
                        try:
                            val = cd.evalPoint(env)
                        except Exception as e:
                            #ignore these no data
                            #traceback.print_exc()
                            cd.error = e
                            curvedatas.remove(cd)
                        else:
                            cd.addPoint(val)
                else:
                    break
        return
    
    
    def getSampleData(self):
        """
        Returns a full sample of all the data that this DataManager supports.
        """
        return self._lastSamples
    
    
    def close(self):
        """
        Clean up and remove and close off all data sources.
        """
        while self._sources:
            item = self._sources.popitem()
            item[1][0].close()