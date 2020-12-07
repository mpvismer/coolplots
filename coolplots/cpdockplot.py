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
import time

try:
    from .support import *
    from .legenditemmod import LegendItemMod
    from .cpcurve import *
    from .curveproperties import CurveProperties
except:
    from support import *
    from legenditemmod import LegendItemMod
    from cpcurve import *
    from curveproperties import CurveProperties

from pyqtgraph.multiprocess.remoteproxy import ObjectProxy


class PlotCurveItemMod(pg.PlotCurveItem):
    """
    A PlotCurveItem with built in profiling
    """
    def __init__(self, *args, **kargs):
        super(PlotCurveItemMod, self).__init__(*args, **kargs)
        self._prof = utils.Profiler()
    
    def paint(self, p, opt, widget):
        self._prof.lapStart()
        ret = super(PlotCurveItemMod, self).paint(p, opt, widget)
        self._prof.lapEnd()
        return ret


PLOTS = weakref.WeakValueDictionary()

class CpDockPlot(Dock):
    """
    A dockable plotting window.
    """
    
    plotCount = 0
    colours = ['b', 'r', 'g', 'c', 'y','w','y']
    
    
    def __init__(self, dataManager, title=None, curves=[], *args, **kargs):
        """ Constructor. """
        #if title in CpDockPlot.plots:
        #    raise Exception("Plot title already exists.")
        self._dataManager = dataManager
        kargs['closable'] = True
        kargs['size'] = (300, 300)
        super(CpDockPlot, self).__init__(*args, name=title or "<no title>", **kargs)
        self.label.updateStyle = lambda: labelUpdateStyle(self.label)
        self.streamData = None
        self.curves = collections.OrderedDict()
        self.plotDataItems = {}
        self.legendDirection = 'vertical'
        self.colourIndex = 0
        self.streamBufferLen = 2000
        self.linearRegion = None
        self._profFull = utils.Profiler()
        self._prof = utils.Profiler()
        
        #self._makeRemote()
        self._makeLocal()
        self.plotItem.addLegend()
        self.plotItem.setDownsampling(auto=True, mode='peak')
        self.plotItem.setClipToView(True)
        
        self.someText = self.view.pg.LabelItem('~~~~~~~~~~~~~', size='11pt', parent=self.plotItem)
        self.plotItem.layout.addItem(self.someText, 4, 1)
        self.showTimings(False)
        self.view.pg.setConfigOptions(antialias=True)  ## prettier plots at no cost to the main process!
        #self.view.pg.setConfigOptions(useOpenGL=True)
        #view.pg.setConfigOption('leftButtonPan', False)
        ## Create a PlotItem in the remote process that will be displayed locally
        
        #Make the navigator window
        #self.navigator = self.view.pg.ViewBox(parent=self)# self.view.pg.PlotItem()
        #self.navigator.showAxis('bottom', False)
        #layout = self.view.pg.graphicsItems.GraphicsLayout.GraphicsLayout()
        #layout.addItem(self.navigator)
        #layout.nextRow()
        #layout.addItem(self.plot)
        
        self.view.setCentralItem(self.plotItem)
        self.addWidget(self.view)
        notify_destroy(self)
        self._style = """
        * {
            background : red;
            padding-right: 10px;
            /*margin-right: 10px;*/
        }
        """
        #self.setStyleSheet(self._style)
        PLOTS[id(self)] = self
        CpDockPlot.plotCount = CpDockPlot.plotCount + 1
        self.lastDatas = {}
        
        self._globals = globals()
        exec("from numpy import *", self._globals, {})
        
        for cid in curves:
            self.setCurve(cid)
        
        self.toLink = []
    
    
    def _makeLocal(self,):
        from pyqtgraph.widgets.GraphicsView import GraphicsView
        self.view = GraphicsView()
        self.view.pg = pg
        #self.view.pgm = __import__('PlotDataItemMod')
        self.plotItem = self.view.pg.PlotItem(title=self.getTitle(), name=self.getTitle())
    
    
    def _makeRemote(self):
        from pyqtgraph.widgets.RemoteGraphicsView import RemoteGraphicsView
        self.view = RemoteGraphicsView()
        #self.view.pgm = self.view._proc._import('PlotDataItemMod')
        self.plotItem = self.view.pg.PlotItem(title=self.getTitle(), name=self.getTitle())
        self.plotItem._setProxyOptions(deferGetattr=True)  ## speeds up access to memebers
    
    
    def _nextColour(self):
        c = self.colours[self.colourIndex]
        self.colourIndex= (1 + self.colourIndex) % len(self.colours)
        return c
    
    
    def _addNavigatorCurve(self, item):
        if getattr(self, 'navigator', None) is not None:
            if item.fullCurve is None:
                #TODO: subsample because more efficient
                #item.fullCurve = self.view.pg.PlotCurveItem([], pen=item.colour, name=item.name)
                item.fullCurve = PlotCurveItemMod([], pen=item.colour, name=item.name)
                if isinstance(item.fullCurve, ObjectProxy):
                    curve._setProxyOptions(deferGetattr=True)
            self.navigator.addItem(item.fullCurve)
    
    
    def setTitle(self, title):
        """
        Sets the title of the dock plot (after it has been created.
        """
        self.label.setText(title)
        self.plotItem.setTitle(title)
        self.plotItem.vb.register(title)
    
    
    def getTitle(self):
        """
        Return title of this DockPlot
        """
        #only the title in self.label is valid
        return self.name()
    
    
    def showPlotTitle(self, show):
        """
        Show or hide teh title for the plot.
        """
        if show:
            self.plotItem.setTitle(self.getTitle())
        else:
            self.plotItem.setTitle(None)
    
    
    def isPlotTitleVisible(self):
        """
        Return True if the plot title is visible.
        """
        return self.plotItem.titleLabel.isVisible()
    
    
    def showXAxis(self, show=True):
        self.plotItem.showAxis('bottom', show)
    
    
    def isXAxisVisible(self):
        return self.plotItem.getScale('bottom').isVisible()
    
    
    def showYAxis(self, show=True):
        self.plotItem.showAxis('left', show)
    
    
    def isYAxisVisible(self):
        return self.plotItem.getScale('left').isVisible()
    
    
    def showTimings(self, show=True):
        if show:
            self.someText.setMaximumHeight(30)
            self.plotItem.layout.setRowFixedHeight(4, 30)
            self.someText.setVisible(True)
        else:
            self.someText.setVisible(False)
            self.plotItem.layout.setRowFixedHeight(4, 0)
            self.someText.setMaximumHeight(0)
    
    
    def isTimingsVisible(self):
         return self.someText.isVisible()
    
    
    def showLegend(self, show, direction=None):
        if show:
            offset = self.plotItem.legend.pos()
            #print(offset)
            if self.plotItem.legend:
                self.plotItem.legend.close()
            #self.plot.addLegend()
            self.legendDirection = direction or self.legendDirection
            self.plotItem.legend = LegendItemMod(None, offset, direction=self.legendDirection)
            self.plotItem.legend.setParentItem(self.plotItem.vb)
            for cid in self.curves.keys():
                self.plotItem.legend.addItem(self.plotDataItems[cid], self.curves[cid].name)
                owner = self.plotItem.legend.items[-1][0]
                owner.mouseClickedEvent = partial(self.toggleCurveVisible, cid)
                owner = self.plotItem.legend.items[-1][1]
                owner.mouseClickEvent = partial(self.showCurveContextMenu, cid)
        elif not self.plotItem.legend is None:
            self.plotItem.legend.hide()
            #self.plotItem.legend = None
    
    
    def isLegendVisible(self):
        """
        Returns True is visible else False
        """
        return self.plotItem.legend.isVisible()
    
    
    def makeLinearRegion(self, region=None):
        if self.linearRegion is None:
            self.linearRegion = pg.LinearRegionItem([0, 1])
            self.linearRegion.setZValue(+50)
            self.linearRegion.linkedPlots = []
            self.plotItem.addItem(self.linearRegion)
            if region:
                self.linearRegion.setRegion(region)
    
    
    def linkPlot(self, dockPlot):
        """
        Creates a linear region linked to <plot>
        """
        assert dockPlot is not self
        if dockPlot is None:
            self.plotItem.removeItem(self.linearRegion)
            self.linearRegion = None
        else:
            self.makeLinearRegion(dockPlot.plotItem.getViewBox().viewRange()[0])
            self.linearRegion.linkedPlots.append(dockPlot.getTitle())
            print("Linking region in %s to %s." % (self.getTitle(), dockPlot.getTitle()))
            dockPlot.updateXRangeFromRegion(self.linearRegion)
            self.linearRegion.sigRegionChanged.connect(dockPlot.updateXRangeFromRegion)
            dockPlot.plotItem.sigXRangeChanged.connect(partial(self.updateRegionFromPlot, dockPlot.plotItem))
    
    
    def updateXRangeFromRegion(self, region):
        self.plotItem.setXRange(*region.getRegion(), padding=0, update=False)
    
    def updateRegionFromPlot(self, plotItem):
#        if self.linearRegion is None:
        self.linearRegion.setRegion(plotItem.getViewBox().viewRange()[0])
    
    
    def makePlotMenu(self):
        """
        Make the plotting menu which allows selecting what to plot from data manager.
        """
        def addFieldIndex(menu, data, accessor):
            for idx, val in enumerate(data):
                title = '[%u]'%idx
                newaccessor = accessor+title
                addField(menu, val, newaccessor, title)
        
        def addFieldCls(menu, cls, accessor):
            for fieldName, val in cls_fields(cls):
                newaccessor = accessor+'.'+fieldName
                addField(menu, val, newaccessor, fieldName)
        
        def addField(menu, val, accessor='', title=None):
            if hasattr(val, '__getitem__') and not utils.isstr(val):
                if title:
                    menu = menu.addMenu(title)
                addFieldIndex(menu, val, accessor)
            elif hasattr(val, '__dict__'):
                if title:
                    menu = menu.addMenu(title)
                addFieldCls(menu, val, accessor)
            else:
                action = QtGui.QAction(str(title or '<unamed>'), self )
                action.triggered.connect(partial(self.setCurve, curveid=None, y_expr=accessor))
                menu.addAction(action)
        
        def makeDataMenu(data, menu=None):
            if menu is None:
                menu = QtGui.QMenu("New", self, enabled=False)
            if len(data) == 1:
                menu.setEnabled(True)
                for key,val in data.iteritems():
                    addField(menu, val=val, accessor=key)
            elif len(data) > 1:
                menu.setEnabled(True)
                for key,val in data.iteritems():
                    nmenu = menu.addMenu(key)
                    addField(nmenu, val=val, accessor=key)
        
        datas = self._dataManager.getSampleData()
        menuTop = QtGui.QMenu("New", self, enabled=False)
        if len(datas)==1:
            makeDataMenu(datas['default'], menuTop)
        elif len(datas) > 1:
            menu.setEnabled(True)
            for key, data in datas.items():
                menu = menuTop.addMenu(key, enabled=False)
                makeDataMenu(data, menu)
        return menuTop
        #menu.popup(self.mapToGlobal(QtCore.QPoint(25,25)))
    
    
    def showPlotMenu(self):
        menu = QtGui.QMenu(self)
        new = self.makePlotMenu()
        menu.addMenu(new)
        menu.addSeparator()
        for key, item in CURVES.items():
            action = QtGui.QAction(item.name, self, triggered=partial(self.setCurve, key))
            menu.addAction(action)
        menu.popup(self.mapToGlobal(QtCore.QPoint(25,25)))
    
    
    def showEditCurveMenu(self):
        menu = QtGui.QMenu(self)
        for key, item in self.curves.items():
            action = QtGui.QAction(item.name, menu, triggered=partial(self.curveProperties, key))
            menu.addAction(action)
        menu.addSeparator()
        action = QtGui.QAction("New", menu, triggered=lambda:self.curveProperties())
        menu.addAction(action)
        menu.popup(self.mapToGlobal(QtCore.QPoint(25,25)))
        pass
    
    
    def showLinkMenu(self):
        menu = QtGui.QMenu(self)
        for item in PLOTS.values():
            if item is not self:
                action = QtGui.QAction(item.getTitle(), self, triggered=partial(self.linkPlot, item))
                if self.linearRegion is not None:
                    action.setCheckable(True)
                    action.setChecked(self.linearRegion.linkedPlots.count(item.getTitle())>0)
                menu.addAction(action)
        menu.addSeparator()
        action = QtGui.QAction("Remove", self, triggered=partial(self.linkPlot, None), enabled=self.linearRegion is not None)
        menu.addAction(action)
        menu.popup(self.mapToGlobal(QtCore.QPoint(25,25)))
    
    
    def toggleCurveVisible(self, plotDataItem, ev):
        if ev:
            ev.accept()
        #print('what')
        if plotDataItem.isVisible():
            plotDataItem.hide()
        else:
            plotDataItem.show()
    
    
    def showCurveContextMenu(self, cpcurve_id, ev=None):
        if ev:
            ev.accept()
            pt = ev.scenePos()
            pos = QtCore.QPoint(pt.x()+15, pt.y())
        else:
            pos = QtCore.QPoint(25,25)
        menu = QtGui.QMenu(self)
        action = QtGui.QAction("Edit", menu, triggered=partial(self.curveProperties, cpcurve_id))
        menu.addAction(action)
        item = self.plotDataItems[cpcurve_id]
        action = QtGui.QAction("Hide" if item.isVisible() else "Show", menu, triggered=partial(self.toggleCurveVisible, item))
        menu.addAction(action)
        action = QtGui.QAction("Delete", menu, triggered=partial(self.removeCurve, cpcurve_id))
        menu.addAction(action)
        menu.addSeparator()
        action = QtGui.QAction("New", menu, triggered=partial(self.curveProperties))
        menu.addAction(action)
        menu.popup(self.mapToGlobal(pos))
    
    
    def curveProperties(self, curveid=None):
        """
        Typically called by in repsonce to menu actions to
        """
        if curveid is None:
            c = CpCurve(name="New Plot", y_expr='0')
        else:
            c = CURVES[curveid]
        if CurveProperties(c).exec_():
            self.setCurve(id(c))
    
    
    def setCurve(self, curveid=None, **kwargs):
        """
        Add a curve to this plot.
        """
        if curveid is None:
            cpcurve = CpCurve(**kwargs)
            curveid = id(cpcurve)
        elif isinstance(curveid, CpCurve):
            cpcurve = curveid
            curveid = id(cpcurve)
        else:
            cpcurve = CURVES[curveid]
        
        if not hasattr(cpcurve, "_plotDataSource"):
            cpcurve._plotDataSource = self._dataManager.createCurveData(expr=cpcurve.y_expr)
        elif cpcurve._plotDataSource.getExpr()!=cpcurve.y_expr:
            cpcurve._plotDataSource.setExpr(cpcurve.y_expr)
            print("TODO: technically should clear data...")
        
        if not cpcurve.penColour:
            colours = [x.penColour for x in self.curves.values()]
            for i in range(0, len(self.colours)):
                col = self._nextColour()
                if colours.count(col)==0:
                    cpcurve.penColour = col
                    break
            if not cpcurve.penColour:
                cpcurve.penColour = self._nextColour()
        
        if not curveid in self.plotDataItems:
            curve = self.view.pg.PlotDataItem([])
            if isinstance(curve, ObjectProxy):
                curve._setProxyOptions(deferGetattr=True)
            self.plotItem.addItem(curve)
            self.plotDataItems[curveid] = curve
        curve = self.plotDataItems[curveid]
        curve.opts.update(cpcurve.getOpts())
        #curve.invalidateBounds()
        #curve.update()
        
        self.curves[curveid] = cpcurve
        
        self.showLegend(self.isLegendVisible())
    
    
    def removeCurve(self, curveid):
        """
        Removes a curve from the PlotItem.
        """
        curve = self.plotDataItems.pop(curveid)
        self.plotItem.removeItem(curve)
        self.curves.pop(curveid)
        self.showLegend(self.isLegendVisible())
    
    
    def clearPlot(self):
        """
        Clear all the data from the plot.
        """
        for curveid in self.curves.keys():
            self.removeCurve(curveid)
    
    
    def resetPlot(self):
        for key, cpcurve in self.curves.iteritems():
            cpcurve._plotDataSource.clearData()
        self.updatePlots()
    
    
    def updatePlots(self):
        if self.toLink:
            for link in self.toLink:
                for plot in PLOTS.values():
                    if link == plot.getTitle():
                        self.linkPlot(plot)
            self.toLink = []
        
        self._profFull.lapStart()
        for key, curve in self.plotDataItems.items():
            item = self.curves[key]
            y = item._plotDataSource.getData()
            if len(y) > 1:
                curve.setData(y)
                curve.setPos(-len(y), 0)
        self._profFull.lapEnd()
        msg = "updatePlots> " + str(self._profFull)
        #msg += "     paint> " +str(litem.fullCurve._prof)
        self.someText.setText(msg)
    
    
    def getSettings(self):
        """ Gets the settings of this plot. """
        l = []
        for cid, item in self.curves.items():
            d = item.getSettings()
            l.append(d)
        d = {
            'curves': l,
            'showLegend': self.isLegendVisible(),
            'legendOffset': self.plotItem.legend.pos(),
            'legendDirection': self.legendDirection,
            'showPlotTitle': self.isPlotTitleVisible(),
            'showXAxis': self.isXAxisVisible(),
            'showYAxis': self.isYAxisVisible(),
            'plotState': self.plotItem.saveState(),
            'visibles': [item.isVisible() for item in self.plotDataItems.values()],
        }
        if self.linearRegion is not None:
            d['linkedPlots'] = self.linearRegion.linkedPlots
            #d['linearRegion'] = self.linearRegion.getRegion()
        return d
    
    
    def setSettings(self, settings=None, **kwargs):
        """
        Apply/set settings from getSettings()
        """
        if settings is None:
            settings = kwargs
        self.clearPlot()
        if 'showLegend' in settings:
            self.showLegend(settings['showLegend'])
        if 'showPlotTitle' in settings:
            self.showPlotTitle(settings['showPlotTitle'])
        if 'showXAxis' in settings:
            self.showXAxis(settings['showXAxis'])
        if 'showYAxis' in settings:
            self.showYAxis(settings['showYAxis'])
        if 'legendOffset' in settings:
            self.plotItem.legend.autoAnchor(settings['legendOffset'])
        self.legendDirection = settings.get('legendDirection', 'vertical')
        if 'linkedPlots' in settings:
            self.toLink = settings['linkedPlots']
        #if 'linearRegion' in settings:
        #    self.makeLinearRegion(settings['linearRegion'])
        if 'plotState' in settings:
            self.plotItem.restoreState(settings['plotState'])
        curves = settings.get('curves',[])
        for d in curves:
            curveid = None
            for key, curve in CURVES.items():
                if d==curve.getSettings():
                    curveid = key
            self.setCurve(curveid=curveid, **d)
        if 'visibles' in settings:
            for state, item in zip(settings['visibles'], self.plotDataItems.values()):
                if state:
                    item.show()
                else:
                    item.hide()
    
    def keyReleaseEvent(self, ev):
        ch = str(ev.text()).upper()
        if ch == 'F':
            self.float()
        elif ch == 'R':
            self.resetPlot()
        elif ch == 'C':
            self.clearPlot()
        elif ch == 'P':
            self.showPlotMenu()
        elif ch == 'E':
            self.showEditCurveMenu()
        elif ch == 'G':
            self.showLegend(not self.isLegendVisible())
        elif ch == 'H':
            self.showLegend(True, direction='horizontal')
        elif ch == 'V':
            self.showLegend(True, direction='vertical')
        elif ch == 'T':
            self.showPlotTitle(not self.isPlotTitleVisible())
        elif ch == 'X':
            self.showXAxis(not self.isXAxisVisible())
        elif ch == 'Y':
            self.showYAxis(not self.isYAxisVisible())
        elif ch == 'I':
            self.showTimings(not self.isTimingsVisible())
        elif ch == 'Q':
            self.showLinkMenu()
        elif ch == 'D':
            self.area.addDock(
                CpDockPlot(self._dataManager, curves=self.curves.keys(), title='_'+self.getTitle()),
                position='bottom',
                relativeTo=self)
        else:
            return super(CpDockPlot, self).keyReleaseEvent(ev)
        
        gc.collect()
    
    
    def containerChanged(self, c):
        super(CpDockPlot, self).containerChanged(c)
        if self.area is not None:
            self.area.removeDock(self)
        c.area.docks[self.name()] = self
        #c.area.setSettings()
    
    
    def close(self):
        if self.linearRegion is not None:
            try:
                self.linearRegion.sigRegionChanged.disconnect()
            except:
                traceback.print_exc()
        
        self.clearPlot()
        self.area.removeDock(self)
        super(CpDockPlot, self).close()
        self.label.dock = None
        #self.destroy()
        gc.collect()



def labelUpdateStyle(self):
    if self.dim:
        fg = 0xaaa
        bg1 = 0x339
        bg2 = 0x338
        border = 0x55c
    else:
        fg = 0xeee
        bg1 = 0x2af
        bg2 = 0x35E
        border = 0x7af
    #self.hint = QtCore.QSize(50,30)
    
    self.setProperty("orientation", self.orientation)
    style = """
    QToolButton {
        background : transparent
    }
    DockLabel {
        color: #%x;
        border-radius: 0px;
    }
    DockLabel[orientation="horizontal"] {
        background: qlineargradient(x1:0, y1:1, x2:1, y2:1,
                stop:0 #%x, stop: 0.6 #%x);
        /* padding-left: 3px;
        padding-right: 3px;
        border-top: 2px solid #55c;*/
    }
    DockLabel[orientation="vertical"] {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                stop:0 #%x, stop: 0.6 #%x);
        /* padding-top: 3px;
        padding-bottom: 3px;
        border-left: 2px solid #55c;*/
    }
    DockLabel:hover {
        border: 1px solid #%x;
    }
    QToolButton:hover {
        border: 1px solid #%x;
        background: #%x;
    }
    """ % (fg, bg1, bg2, bg1, bg2, border, border, bg1)
    self.setStyleSheet(style)


def cls_fields(cls):
    """
    Returns the non-hidden attributes of a class.
    """
    #for member in dir(cls):
    for member, val in inspect.getmembers(cls):
        if not callable(val) and not member.startswith('_'):
             yield (member, val)



if __name__ == '__main__':
    if QtGui.QApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
    
    iconpath = 'cmr_logo_64x64.xpm'
    try:
        app.setWindowIcon(QtGui.QIcon(iconpath))
    except Exception, e:
        print ("Unable to load icon", iconpath, ":", e)
    
    #newWin = QMainWindow()
    #newWin.setCentralWidget(DockPlot(name='test', title='Test Plotter'))
    newWin = CpDockPlot(None)
    newWin.show()
    
    exitCode = app.exec_()
    
    sys.exit(exitCode)
    
