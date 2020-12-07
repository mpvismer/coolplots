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
    from .cpdockplot import CpDockPlot
except:
    from support import *
    from cpdockplot import CpDockPlot

#from pyqtgraph.multiprocess.remoteproxy import ObjectProxy

_logger = utils.get_logger(__name__)


class CpDockArea(DockArea):
    """
    Derived from the pyqtgraph DockArea, it holds CpDockPlot's which can be
    docked in different ways.
    """
    areaCount = 0
    areas = []
    mainWindow = None
    
    #areaClass = CpMainWindowContainer
    
    def __init__(self, dataManager, title=None, autoclose=True, **kwargs):
        """
        autoclose - When the last plot in this plot is closed, also close the
        """
        super(CpDockArea, self).__init__(**kwargs)
        if not title:
            CpDockArea.areaCount += 1
            title = 'Plot Area %i'%CpDockArea.areaCount
        self._dataManager = dataManager
        self.setWindowTitle(title)
        self.autoclose = autoclose
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self._styleHideSplitters = """
        QSplitter::handle {
            background : black;
        }
        QSplitter::handle:horizontal {
            width: 10px;
        }
        QSplitter::handle:vertical {
            height: 10px;
        }
        QSplitter[orientation="1"]::handle:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1af, stop: 0.6 #25E);
        }
        
        QSplitter[orientation="2"]::handle:pressed {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #1af, stop: 0.6 #25E);
        }
        """
        self._styleShowSplitters = """
        QSplitter[orientation="1"]::handle {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1af, stop: 0.6 #25E);
        }
        
        QSplitter[orientation="2"]::handle {
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #1af, stop: 0.6 #25E);
        }
        """
        self._settings = { "locked" : False, "frame" : True}
        self.setSettings()
        notify_destroy(self)
    
    #def showEvent(self, ev):
    #    self.setFocus(QtCore.Qt.MouseFocusReason) # doesnt seem to work :(
    #    return super(CpDockArea, self).showEvent(ev)
    
    def updateStyle(self):
        if self._settings["locked"]:
            self.setStyleSheet(self._styleHideSplitters)
        else:
            self.setStyleSheet(self._styleShowSplitters)
    
    
    def setSettings(self, settings=None):
        if settings is not None:
            self._settings.update(settings)
            #print(settings)
        if (self._settings['locked']):
            self.lock()
        else:
            self.unlock()
        if self._settings['frame']:
            self.showFrame()
        else:
            self.hideFrame()
        #self.showTitles(self._settings['titles'])
    
    
    def getSettings(self):
        return self._settings
        #return {'settings' : self._settings, 'state': self.saveState() }
    
    
    def addDock(self, dock=None, position='right', relativeTo=None, **kwargs):
        """ Creates a new plot. """
        if dock is None:
            title = 'Plot'
            dock = CpDockPlot(self._dataManager, title)
        else:
            title = dock.getTitle()
        
        count = 1;
        newtitle = title
        while newtitle in self.docks:
            if self.docks[newtitle]==dock:
                break
            newtitle = title + " %i" % count
            count += 1
        
        if title!=newtitle:
            warnings.warn('CpDockPlot "%s" already existed, renaming to "%s"...' % (title, newtitle) )
            dock.setTitle(newtitle)
        return super(CpDockArea, self).addDock(dock, position, relativeTo, **kwargs)
    
    
    def removeDock(self, dock):
        """
        When a dock is removed, need to remove from self.
        """
        if dock.name() in self.docks:
            self.docks.pop(dock.name())
    
    
    def lock(self):
        """
        Lock the DockPlots in this area - the CpDockPlots cannot be moved
        and the tabs are not visible.
        """
        self._settings['locked'] = True
        for plot in self.docks.values():
            plot.hideTitleBar()
        self.updateStyle()
        if hasattr(self, 'win'):
            pass
            #self.win.setStyleSheet("background:transparent;");
        #w = self.parentWidget()
        #w.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint);
        #w.setWindowFlags ( w.windowFlags() | QtCore.Qt.FramelessWindowHint)
    
    
    def unlock(self):
        """
        Unlock the DockPlots and mkae the tabs visible.
        """
        self._settings['locked'] = False
        for dock in self.docks.values():
            dock.showTitleBar()
        self.updateStyle()
    
    
    def hideFrame(self):
        self._settings['frame'] = False
        w = self.parentWidget()
        if w is not None:
            newFlags = QtCore.Qt.FramelessWindowHint | w.windowType()
            if w.windowFlags()!=newFlags:
                w.setWindowFlags(newFlags);
            #w.setWindowFlags ( w.windowFlags() | QtCore.Qt.FramelessWindowHint)
            w.show()
            w.setFocus(QtCore.Qt.MouseFocusReason)
            self.setFocus(QtCore.Qt.MouseFocusReason)
    
    
    def showFrame(self):
        self._settings['frame'] = True
        w = self.parentWidget()
        if w is not None:
            newFlags = w.windowType()
            if w.windowFlags()!=newFlags:
                w.setWindowFlags(newFlags);
            w.show()
            w.setFocus(QtCore.Qt.MouseFocusReason)
            self.setFocus(QtCore.Qt.MouseFocusReason)
    
    def showTitles(self, show):
        self._settings['titles'] = show
        for title, dock in self.docks.iteritems():
            dock.showPlotTitle(show)
        self.updateStyle()
    
    
    def updatePlotData(self, data, x_val=None):
        """
        Unlock the DockPlots and mkae the tabs visible.
        """
        for plot in self.docks.values():
            plot.updatePlotData(data, x_val)
    
    
    def keyReleaseEvent(self, ev):
        """
        Handles key presses in the main window
        """
        ch = str(ev.text()).upper()
        if ch == 'N':
            self.addDock()
        elif ch == 'L':
            if self._settings['locked']:
                self.unlock()
            else:
                self.lock()
        elif ch == 'W':
            if self._settings['frame']:
                self.hideFrame()
            else:
                self.showFrame()
        return super(CpDockArea, self).keyReleaseEvent(ev)
    
    def removeTempArea(self, area):
        """
        Overrides
        """
        if self.home is None:
            #print("removeTempArea/window", area,  area.window())
            _logger.debug('Removing temp area "%s"...' % area)
            if CpDockArea.mainWindow is not None:
                if area in self.mainWindow.dockedPanels.values():
                    ret = self.mainWindow.removeDockablePanel(area)
                    assert ret == area
            self.tempAreas.remove(area)
            area.window().close()
        else:
            self.home.removeTempArea(area)
    
    def addTempArea(self):
        """
        Overrides - no longer used.
        """
        if self.home is None:
            area = CpDockArea(self._dataManager, temporary=True, home=self)
            #print("addTempArea/window", area,  area.window())
            self.tempAreas.append(area)
            if CpDockArea.mainWindow is not None:
                win = self.mainWindow.addDockablePanel(area)
            else:
                win = QtGui.QMainWindow()
                win.setCentralWidget(area)
                CpDockArea.mainWindow = win
            #win.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            area.win = win
            win.show()
        else:
            area = self.home.addTempArea()
        #print "added temp area", area, area.window()
        return area
    
    
    def buildFromState(self, state, docks, root, depth=0):
        if state is not None:
            typ, contents, settings = state
            if typ == 'dock':
                if not contents in docks:
                    docks[contents] = CpDockPlot(self._dataManager, title=contents, closable=True)
                    docks[contents].setSettings(settings)
                    docks[contents].area = self
            return super(CpDockArea, self).buildFromState(state=state, docks=docks, root=root, depth=depth)
    
    def childState(self, obj):
        if isinstance(obj, Dock):
            return ('dock', obj.name(), obj.getSettings())
        else:
            if obj is not None:
                return super(CpDockArea, self).childState(obj)
            else:
                return None
    
    
    def apoptose(self):
        _logger.debug('apoptose up for "%s"...' % self)
        #print "apoptose area:", self.temporary, self.topContainer, self.topContainer.count()
        if self.topContainer.count() == 0:
            self.topContainer = None
            if self.temporary:
                self.home.removeTempArea(self)
        self.close()
    
    
    def closeEvent(self, event):
        """
        Need to handle cleanup.
        """
        _logger.debug('Cleaning up CpDockArea "%s"...' % self.windowText())
        for plot in self.docks.values():
            plot.close()
        return super(CpDockArea, self).closeEvent(event)



if __name__ == '__main__':
    
    if QtGui.QApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
    
    win = CpDockArea(title='Test Plotter')
    win.addDock()
    win.show()
    
    exitCode = app.exec_()
    
    sys.exit(exitCode) 
