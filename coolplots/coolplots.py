"""
Original work Copyright (c) 2015 Mark Vismer

A tool for managing and plotting data. Runs on top of the Qt4 framework.

pyqtgraph is used for the underlying plot manager and drawer - though the
intention is to abstract this out at some point.

Shortcut Keys:

Ctrl+N New PLot in the main window.
Ctrl+L Toggle lock of all windows based on the main window state

Controls
~~~~~~~~~~
Plots:
P - Plot menu (of parameters to plot)
E - Edit plots.
C - Clear, remove all curves from a plot.
R - Reset data, empty recorded data. Flush buffers and restart.
F - Float the plot window
G - Toggle legend on off
H - Show legend with horizontal layout
V - Show legend with vertical layout
T - Toggle plot titles
X - Toggle X axis on/off
Y - Toggle Y axis on/off
Q - Add navigation view.
D - Duplicate plot.

MouseWheel on axis, zooms that axis in or out.
MouseWheel on plot zooms the entire plot in or out.
LMB drag on axis to move the plot on that axis.
LMB drag on plot to move plot.

N - Add a new plot to the current window
L - Toggle lock of the current window (hides DockPlot bars).
W - Toggle window frame (meant to toggle transparency too? - not working yet)


Known bugs:
~~~~~~~~~~~
Panel names not saved
When closing a panel, then creating a new with f key, the title is Plot Data 2
but there is only one panel - so when loaded next time the name is Plot Data 1
because names are not saved

Unexpect application exit when closing DockPlots in a QtDock
If plots are insided a Qt Dock and then the Qt dock is docked in the main window,
when closing the DockPlots such that the Qt Dock becomes empty (and tries to close),
the TopWindow closes as well :(..
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import math
import weakref
import time
#import copy
#from functools import partial
import logging
import gc
import numpy as np
import traceback


try:
    from .support import *
    from .cpdockplot import CpDockPlot, PLOTS
    from .cpdockarea import CpDockArea
    from .curvedata import *
    from .datamanager import *
except ValueError as e:
    from support import *
    from cpdockplot import CpDockPlot, PLOTS
    from cpdockarea import CpDockArea
    from curvedata import *
    from datamanager import *

import qtk
#from qtk.controls.classviewer import ClassViewer
import h2pyex



_logger = utils.get_logger(__name__)

class CoolPlots(qtk.MainWindow):
    """
    The top level window which handles adding and removing docks.
    """
    
    def __init__(self, dataManager, **kwargs):
        """ Constructor. """
        sessionFilename = kwargs.get('sessionFilename','default.session')
        kwargs['sessionFilename']=''
        super(CoolPlots, self).__init__(**kwargs)
        self.count = 0
        
        self._dataManager = dataManager
        CpDockArea.mainWindow = self
        self.mainPlotArea = CpDockArea(self._dataManager, title='Primary Plot', temporary=False)
        
        #self.addDockablePanel(self.plotArea)
        self.setCentralWidget(self.mainPlotArea)
        
        #self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        #self.addAction(QtGui.QAction(str('Test'), self))
        
        self.actionNew = QtGui.QAction(
            'New',
            self,
            shortcut = 'Ctrl+N',
            triggered = lambda: self.mainPlotArea.addDock(),
            statusTip = (self.mainPlotArea.addDock.__doc__ or '').strip(' \r\n') )
        
        self.actionLock = QtGui.QAction(
            'Lock Plots',
            self,
            shortcut = 'Ctrl+L',
            checkable = True,
            toggled = lambda: self.toggleLock(),
            statusTip = (self.toggleLock.__doc__ or '').strip(' \r\n') )
        
        self.actionTest = QtGui.QAction(
            'Test',
            self,
            shortcut = 'Ctrl+T',
            triggered = lambda: self.toggleLock(),
            statusTip = (self.toggleLock.__doc__ or '').strip(' \r\n') )
        
        self.plotMenu = self.menuBar().addMenu('&Plot')
        self.plotMenu.addAction(self.actionNew)
        self.plotMenu.addAction(self.actionLock)
        self.plotMenu.addAction(self.actionTest)
        
        if sessionFilename:
            if os.path.isfile(sessionFilename):
                self.loadSessionFile(sessionFilename)
    
    
    def startUpdates(self):
        ts = time.time()
        self._lastTime = ts
        self._printTime = ts
        self._guiTime = ts
        self._fps = 1
        
        self.tick = QtCore.QTimer()
        self.tick.timeout.connect(self.updatePlotsTick)
        self.tick.setSingleShot(True)
        self.tock = QtCore.QTimer()
        self.tock.timeout.connect(self.idleTock)
        self.tock.setSingleShot(True)
        
        self.tick.start(50)
    
    
    def updatePlotData(self, count=None):
        """
        Signal each plot to fetch new data and redraw.
        """
        for plot in PLOTS.values():
            plot.updatePlots()
    
    
    def updatePlotsTick(self):
        now = time.time()
        
        self._dataManager.updateCurveData()
        
        #prof.lapStart()
        win.updatePlotData()
        #prof.lapEnd()
        
        dt = now - self._lastTime + 1e-12
        self._lastTime = now
        if self._fps is None:
            self._fps = 1.0/dt
        else:
            s = max(dt*2., 1)
            self._fps = self._fps * (1-s) + (1.0/dt) * s
        if now-self._guiTime>0.1:
            self._guiTime = now
            win.setWindowTitle('CoolPlots - %0.2f fps' % self._fps)

#        if now-self._printTime>1:
#            self._printTime = now
#            print("Toto> " + str(prof))
        
        
        self.tock.start(5)
    
    
    def idleTock(self):
        self.tick.start(5)
    
    
    def getSessionSettings(self):
        settings = super(CoolPlots, self).getSessionSettings()
        settings['coolplots'] = self.mainPlotArea.saveState()
        #print(settings['coolplots'])
        return settings
    
    
    def setSessionSettings(self, settings):
        cool = settings.get('coolplots', None)
        #print(cool)
        if cool:
            _logger.info("Applying coolplots settings.")
            try:
                self.mainPlotArea.restoreState(cool)
            except:
                traceback.print_exc()
                print("Error loading coolplots settings.")
        super(CoolPlots, self).setSessionSettings(settings)
    
    
    def toggleLock(self, size=(300, 300)):
        """ Toggles the dock control tabs allowing or preventing changes to the layout. """
        
        if self.actionLock.isChecked():
            self.mainPlotArea.lock()
            for area in self.mainPlotArea.tempAreas:
                area.lock()
        else:
            self.mainPlotArea.unlock()
            for area in self.mainPlotArea.tempAreas:
                area.unlock()
    
    
    def closeEvent(self, event):
        """
        Called when the window is closed.
        """
        _logger.debug('Cleaning up TopWindow...')
        
        res =  super(CoolPlots, self).closeEvent(event)
        gc.collect()
        event.accept()
        for plot in list(PLOTS.values()):
            plot.close()
        
        gc.collect()
        gc.collect()
        QtGui.QApplication.instance().quit()
        return res



if __name__ == '__main__':
    filename, file_extension = os.path.splitext(__file__)
    utils.configure_rotating_logging(
        filename+'.log',
        level=getattr(logging, "DEBUG"), maxBytes=128*1024)
    
    if QtGui.QApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
    
    
    iconpath = 'my logo'
    try:
        app.setWindowIcon(QtGui.QIcon(iconpath))
    except Exception, e:
        print ("Unable to load icon", iconpath, ":", e)
    
    dataManager = DataManager(CurveData)
    dataManager.addDataSource(SampleDataSource)
    win = CoolPlots(dataManager=dataManager, title='CoolPlots', panelsToDock=[pg.DataTreeWidget(data=dataManager.getSampleData())])
    win.show()
    win.startUpdates()
    
    app.exec_()