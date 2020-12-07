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
import warnings
import gc

try:
    from .support import *
except:
    from support import *

#from pyqtgraph.multiprocess.remoteproxy import ObjectProxy

_logger = utils.get_logger(__name__)




class CurveProperties(QtGui.QDialog):
    
    def __init__(self, curve):
        super(CurveProperties, self).__init__()
        filepath = os.path.join(__file__,"../curveproperties.ui")
        uic.loadUi(filepath, self)
        self.ebxName.setText(curve.name or '')
        self.ebxY.setText(curve.y_expr or '')
        self.ebxX.setText(curve.x_expr if curve.x_expr else '')
        self.ebxWidth.setValue(curve.penWidth)
        self.penBtn = pg.ColorButton(color=pg.mkPen(color=curve.penColour).color())
        self.formLayout.addRow('Colour', self.penBtn)
        self.curve = curve
        print(curve._plotDataSource.error)
        print(curve._plotDataSource.sourceName)
    
    
    def accept(self):
        self.curve.name = str(self.ebxName.text())
        self.curve.y_expr = str(self.ebxY.text())
        self.curve.x_expr = str(self.ebxX.text())
        self.curve.penColour = self.penBtn.color().name()
        self.curve.penWidth = self.ebxWidth.value()
        return super(CurveProperties, self).accept()




if __name__ == '__main__':
    if QtGui.QApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)

    #newWin = QMainWindow()
    #newWin.setCentralWidget(DockPlot(name='test', title='Test Plotter'))
    newWin = CurveProperties('test', CurveItem())
    print(newWin.exec_())
    
    sys.exit(-1)
            