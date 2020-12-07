"""
Original work from pyqgraph
Modified work Copyright (c) 2015 Mark Vismer

Extensions on the LegendItem
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import copy
from functools import partial
import numpy as np
import threading


try:
    from .support import *
except:
    from support import *

import pyqtgraph.functions as fn

class ItemSample(pg.GraphicsWidget):
    """ Class responsible for drawing a single item in a LegendItem (sans label).
    """
    ## Todo: make this more generic; let each item decide how it should be represented.
    def __init__(self, item):
        pg.GraphicsWidget.__init__(self)
        self.item = item
    
    def boundingRect(self):
        return QtCore.QRectF(0, 0, 20, 20)
    
    def paint(self, p, *args):
        #p.setRenderHint(p.Antialiasing)  # only if the data is antialiased.
        opts = self.item.opts
        
        if opts.get('fillLevel',None) is not None and opts.get('fillBrush',None) is not None:
            p.setBrush(fn.mkBrush(opts['fillBrush']))
            p.setPen(fn.mkPen(None))
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(2,18), QtCore.QPointF(18,2), QtCore.QPointF(18,18)]))
        
        if not isinstance(self.item, pg.ScatterPlotItem):
            p.setPen(fn.mkPen(opts['pen']))
            p.drawLine(2, 18, 18, 2)
        
        symbol = opts.get('symbol', None)
        if symbol is not None:
            if isinstance(self.item, PlotDataItem):
                opts = self.item.scatter.opts
            
            pen = fn.mkPen(opts['pen'])
            brush = fn.mkBrush(opts['brush'])
            size = opts['size']
            
            p.translate(10,10)
            path = pg.drawSymbol(p, symbol, size, pen, brush)


class LegendItemMod(pg.LegendItem):
    """
    Overridden to change colour
    """
    def __init__(self, *args, **kargs):
        direction = kargs.pop('direction', 'horizontal')
        super(LegendItemMod, self).__init__(*args, **kargs)
        self._direction = direction if direction=='horizontal' else 'vertical'
    
    def getDirection(self):
        return self._direction
    
    def addItem(self, item, name):
        """
        Add a new entry to the legend.
        """
        if self._direction=='horizontal':
            label = pg.LabelItem(name)
            if isinstance(item, ItemSample):
                sample = item
            else:
                sample = ItemSample(item)
            self.items.append((sample, label))
            col = self.layout.columnCount()
            self.layout.addItem(sample, 0, col)
            self.layout.addItem(label, 0, col+1)
            self.layout.setColumnFixedWidth(col, 10)
            self.layout.setRowFixedHeight(0, 15)
            self.layout.setColumnFixedWidth(col+2, 12)
            self.updateSize()
        else:
            #row = self.layout.rowCount()
            super(LegendItemMod, self).addItem(item, name)
            self.layout.setColumnFixedWidth(0, 10)
    
    
    def setParentItem(self, p):
        ret = pg.GraphicsWidget.setParentItem(self, p)
        if self.offset is not None:
            offset = pg.Point(self.offset)
            anchorx = 0#1 if offset[0] <= 0 else 0
            anchory = 0#1 if offset[1] <= 0 else 0
            anchor = (anchorx, anchory)
            self.anchor(itemPos=anchor, parentPos=anchor, offset=offset)
        return ret
    
    
    def paint(self, p, *args):
        p.setPen(fn.mkPen(200,200,200,150))
        p.setBrush(fn.mkBrush(20,20,20,150))
        p.drawRect(self.boundingRect())


