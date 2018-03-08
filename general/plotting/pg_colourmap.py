#!/usr/bin/env python

# Name:                         pg_colourmap
#
# Author: Ian Stewart
#
#    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#    Copyright (C) 2018  Ian M Stewart
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    For the GNU General Public License, see <http://www.gnu.org/licenses/>.
#    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

"""
This enables loading, alteration and saving of RGB colourmaps via a GUI interface.
"""

_module_name = 'pg_colourmap'

import os
import numpy as nu
import ppgplot as pgplot

import pgplot_interface as pgi
import draw_widgets as drw
import widgets


#.......................................................................
class HueGraph:
  """
This is an object for recording the relation between hue fraction and colour-index fraction. It behaves like a list of N tuples, each containing a pair (C,H) of floats; the first member of each pair is taken to be the CI fraction, the second is the hue fraction. Really the only reason for making it a class is to enforce certain rules, e.g. that N must be >1; that C must be 0 for the first pair and 1 for the last; that the C values must occur in non-descending order; and that H must be 0<=H<=1.
  """
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, firstH=0.0, lastH=1.0):
    if firstH<0.0 or firstH>1.0:
      raise ValueError('Your firstH value %f is outside the range [0,1].' % (firstH))
    if lastH<0.0 or lastH>1.0:
      raise ValueError('Your lastH value %f is outside the range [0,1].' % (lastH))

    self._firstH = firstH
    self._lastH  = lastH
    self._internalList = []
    self._numPoints = 2+len(self._internalList)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkCiValue(self, ciFrac, prevElementI, nextElementI, force=False):
    prevTuple = self.__getitem__(prevElementI)
    prevCiFrac = prevTuple[0]
    if ciFrac<prevCiFrac:
      if force:
        return prevCiFrac
      else:
        raise ValueError('Your ciFrac %f should be >= the previous value %f.' % (ciFrac, prevCiFrac))

    nextTuple = self.__getitem__(nextElementI)
    nextCiFrac = nextTuple[0]
    if ciFrac>nextCiFrac:
      if force:
        return nextCiFrac
      else:
        raise ValueError('Your ciFrac %f should be <= the subsequent value %f.' % (ciFrac, nextCiFrac))

    return ciFrac

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkHueFrac(self, hueFrac, force=False):
    if hueFrac<0.0:
      if force:
        return 0.0
      else:
        raise ValueError('Your hueFrac value %f is outside the range [0,1].' % (hueFrac))
    if hueFrac>1.0:
      if force:
        return 1.0
      else:
        raise ValueError('Your hueFrac value %f is outside the range [0,1].' % (hueFrac))

    return hueFrac

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def insert(self, elementToReplaceI, chTuple, force=False):
    if elementToReplaceI<1 or elementToReplaceI>self._numPoints-1:
      raise ValueError('%d is not a valid element replacement number.' % (elementToReplaceI))

    (ciFrac, hueFrac) = chTuple

    localCiFrac = self._checkCiValue(ciFrac, elementToReplaceI-1, elementToReplaceI, force)
    localHueFrac = self._checkHueFrac(hueFrac, force)

    self._internalList.insert(elementToReplaceI-1, (localCiFrac,localHueFrac))
    self._numPoints = 2+len(self._internalList)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def delete(self, elementI):
    if elementI<1:
      raise ValueError('You cannot delete the 1st element.')
    if elementI>self._numPoints-1:
      raise ValueError('You cannot delete the last element.')

    self._internalList.pop(elementI-1)
    self._numPoints = 2+len(self._internalList)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __getitem__(self, elementI):
    if elementI<0:
      elementI = self._numPoints + elementI

    if elementI<0 or elementI>self._numPoints-1:
      raise ValueError('%d is not a valid element number.' % (elementI))

    if elementI==0:
      return (0.0,self._firstH)

    if elementI==self._numPoints-1:
      return (1.0,self._lastH)

    return self._internalList[elementI-1]

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __setitem__(self, elementI, chTuple):
    if elementI<0 or elementI>self._numPoints-1:
      raise ValueError('%d is not a valid element number.' % (elementI))

    (ciFrac, hueFrac) = chTuple
    localHueFrac = self._checkHueFrac(hueFrac, force=True)

    if   elementI==0:
      self._firstH = localHueFrac
    elif elementI==self._numPoints-1:
      self._lastH = localHueFrac
    else:
      localCiFrac = self._checkCiValue(ciFrac, elementI-1, elementI+1, force=True)
      self._internalList[elementI-1] = (localCiFrac,localHueFrac)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def unpackValues(self):
    cis  = nu.zeros([self._numPoints],nu.float)
    hues = nu.zeros([self._numPoints],nu.float)
    for i in range(self._numPoints):
      (cis[i],hues[i]) = self.__getitem__(i)

    return (cis,hues)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def interpolate(self, ciFrac):
    if ciFrac<0.0:
      localCiFrac = 0.0
    elif ciFrac>1.0:
      localCiFrac = 1.0
    else:
      localCiFrac = ciFrac

    i0 = 0 # default
    for i in range(self._numPoints-2,0,-1):
      # The sequence is N-2, N-3, ... , 2, 1. 0 is not reached.
      if self.__getitem__(i)[0]<=localCiFrac:
        i0 = i
        break

    (ciFrac0, hueFrac0) = self.__getitem__(i0)
    (ciFrac1, hueFrac1) = self.__getitem__(i0+1)

    hueFrac = hueFrac0 + (hueFrac1 - hueFrac0)*(localCiFrac - ciFrac0)/(ciFrac1 - ciFrac0)

    return hueFrac

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def copy(self):
    newHueGraph = HueGraph(self._firstH, self._lastH)
    newHueGraph._internalList = self._internalList[:]
    newHueGraph._numPoints = 2+len(newHueGraph._internalList)
    return newHueGraph

#.......................................................................
class _Action:
  """
The purpose of the information stored in this class is to enable reconstruction of previous colourmaps.
  """
  _acceptedTypes = ['insert','delete','change']

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, hueI, elementI, typeStr, chTupleOld, chTupleNew):
    if not typeStr in self._acceptedTypes:
      raise ValueError('Type str %s not recognized.' % (typeStr))

    self.hueI       = hueI
    self.elementI   = elementI
    self.typeStr    = typeStr
    self.chTupleOld = chTupleOld
    self.chTupleNew = chTupleNew

#.......................................................................
class InsertAction(_Action):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, hueI, elementI, chTupleNew):
    _Action.__init__(self, hueI, elementI, 'insert', None, chTupleNew)

#.......................................................................
class DeleteAction(_Action):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, hueI, elementI, chTupleOld):
    _Action.__init__(self, hueI, elementI, 'delete', chTupleOld, None)

#.......................................................................
class ChangeAction(_Action):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, hueI, elementI, chTupleOld, chTupleNew):
    _Action.__init__(self, hueI, elementI, 'change', chTupleOld, chTupleNew)

#.......................................................................
class ActionHistory:
  """
For this I want an object that behaves mostly like a list. However I need it to support successive 'undo' or 'redo' operations, and for that two additional variables are required: numUndoableActions and numRedoableActions.
  """
  _doTest=False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self):
    self.actionList = []
    self.numUndoableActions = 0
    self.numRedoableActions = 0

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def append(self, action):
    # This is a little delicate, because we want to add actions to the list starting at self.numUndoableActions. This will only correspond to an unguarded append of self.actionList when the user has done no previous 'undo', i.e. if self.numRedoableActions==0.

    if self._doTest:
      print 'In ActionHistory.append().'

    if self.numRedoableActions>0:
      # Safest is to copy the whole truncated list.
      self.actionList = self.actionList[:self.numUndoableActions]
      if self._doTest:
        print '  Copying existing actionList, new len=', len(self.actionList)

    self.actionList.append(action)
    if self._doTest:
      print '  Appending to actionList, new len=', len(self.actionList)
    self.numUndoableActions += 1
    self.numRedoableActions = 0

    if self._doTest:
      print '  New values:'
      print '  numUndoableActions=', self.numUndoableActions
      print '  numRedoableActions=', self.numRedoableActions

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getLast(self): # choose when undoing
    if self._doTest:
      print 'In ActionHistory.getLast(). Old values:'
      print '  numUndoableActions=', self.numUndoableActions
      print '  numRedoableActions=', self.numRedoableActions

    if self.numUndoableActions<=0:
      return None

    self.numUndoableActions -= 1
    self.numRedoableActions += 1

    if self._doTest:
      print '  New values:'
      print '  numUndoableActions=', self.numUndoableActions
      print '  numRedoableActions=', self.numRedoableActions

    return self.actionList[self.numUndoableActions]

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getNext(self): # choose when redoing
    if self._doTest:
      print 'In ActionHistory.getNext(). Old values:'
      print '  numUndoableActions=', self.numUndoableActions
      print '  numRedoableActions=', self.numRedoableActions

    if self.numRedoableActions<=0:
      return None

    self.numUndoableActions += 1
    self.numRedoableActions -= 1

    if self._doTest:
      print '  New values:'
      print '  numUndoableActions=', self.numUndoableActions
      print '  numRedoableActions=', self.numRedoableActions

    return self.actionList[self.numUndoableActions-1]

#.......................................................................
class ColourMap:
  _defaultRedFirstHue = 0.0
  _defaultGrnFirstHue = 0.0
  _defaultBluFirstHue = 0.0
  _defaultRedLastHue = 1.0
  _defaultGrnLastHue = 1.0
  _defaultBluLastHue = 1.0
  _numHues = 3

  # used for point selection purposes:
  _minCiFrac  = 0.02
  _minHueFrac = 0.02

  _hueNames = ['red','grn','blu']
  _numHues = len(_hueNames)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self):
    self.hueGraphs = []
    self.hueGraphs.append(HueGraph(self._defaultRedFirstHue, self._defaultRedLastHue))
    self.hueGraphs.append(HueGraph(self._defaultGrnFirstHue, self._defaultGrnLastHue))
    self.hueGraphs.append(HueGraph(self._defaultBluFirstHue, self._defaultBluLastHue))

#    self.pointHighlighted = [None,None,None]
    self.selectedHueI = None # valid when clickEvent.showLine==True
    self.selectedElementI = None # valid when clickEvent.showLine==True

    self.actionHistory = ActionHistory()

    # The following are set in self.initialize(widget), which should be called after the gui is constructed but before anything else:
    self.minAvailCI = None
    self.maxAvailCI = None
    self.vpXLo = None
    self.vpXHi = None
    self.vpYLo = None
    self.vpYHi = None
    self.worldXLo = None
    self.worldXHi = None
    self.worldYLo = None
    self.worldYHi = None
    self.xDeltaRatio = None
    self.yDeltaRatio = None

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def initialize(self, gui):
    # This does the initial drawing, but there are some other things which need to be done once just after the GUI has been drawn for the first time and before any callbacks are initiated, e.g. to store the available range of colourmap indices, and to store the viewport size.

    (self.minAvailCI,self.maxAvailCI) = gui.plotter.lowLevelPlotter.getColourIndexRange()
    (self.vpXLo, self.vpXHi, self.vpYLo, self.vpYHi) = pgplot.pgqvp(0)
#    (self.worldXLo, self.worldXHi, self.worldYLo, self.worldYHi) = pgplot.pgqwin() #*** this routine is not available in the version of ppgplot I have.
    self.worldXLo = gui.ranges[0].lo
    self.worldXHi = gui.ranges[0].hi
    self.worldYLo = gui.ranges[1].lo
    self.worldYHi = gui.ranges[1].hi
    self.xDeltaRatio = (self.vpXHi - self.vpXLo)/(self.worldXHi - self.worldXLo)
    self.yDeltaRatio = (self.vpYHi - self.vpYLo)/(self.worldYHi - self.worldYLo)

    self.drawAll(gui)

    gui.plotter.lowLevelPlotter.setColour('white')

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _undo(self, action):
    if   action.typeStr=='insert':
      self.hueGraphs[action.hueI].delete(action.elementI)
    elif action.typeStr=='delete':
      self.hueGraphs[action.hueI].insert(action.elementI, action.chTupleOld)
    else: # assume action.typeStr=='change':
      self.hueGraphs[action.hueI][action.elementI] = action.chTupleOld

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _redo(self, action):
    if   action.typeStr=='insert':
      self.hueGraphs[action.hueI].insert(action.elementI, action.chTupleNew)
    elif action.typeStr=='delete':
      self.hueGraphs[action.hueI].delete(action.elementI)
    else: # assume action.typeStr=='change':
      self.hueGraphs[action.hueI][action.elementI] = action.chTupleNew

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _redrawHueGraph(self, hueI, widget, tupleToErase=None):
    oldFill = widget.gui.plotter.lowLevelPlotter.getFill()
    oldColour = widget.gui.plotter.lowLevelPlotter.getColour()

    if not tupleToErase is None:
      # Draw the start and end points in the frame bkg colour before drawing all points and lines in white:
      colour = widget.parent.widgetPlotter.bgColour
      widget.gui.plotter.lowLevelPlotter.setColour(colour)
      xs = nu.array([tupleToErase[0]])
      ys = nu.array([tupleToErase[1]])
      xs = widget.ranges[0].lo*(1.0 - xs) + widget.ranges[0].hi*xs
      ys = widget.ranges[1].lo*(1.0 - ys) + widget.ranges[1].hi*ys
      pgplot.pgpt(xs, ys, 0) # point type 0 is squares.

    # Draw the canvas background:
    widget.widgetPlotter.draw()

    # Now draw the points and lines:
    widget.gui.plotter.lowLevelPlotter.setColour('white')
    (xs,ys) = self.hueGraphs[hueI].unpackValues()
    xs = widget.ranges[0].lo*(1.0 - xs) + widget.ranges[0].hi*xs
    ys = widget.ranges[1].lo*(1.0 - ys) + widget.ranges[1].hi*ys
    pgplot.pgline(xs, ys)
    pgplot.pgpt(xs, ys, 0) # point type 0 is squares.

    widget.gui.plotter.lowLevelPlotter.setFill(oldFill)
    widget.gui.plotter.lowLevelPlotter.setColour(oldColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _redrawColourBar(self, widget):
    oldFill = widget.gui.plotter.lowLevelPlotter.getFill()
    oldColour = widget.gui.plotter.lowLevelPlotter.getColour()

    widget.gui.plotter.lowLevelPlotter.setFill(True)
    yLo = widget.ranges[1].lo
    yHi = widget.ranges[1].hi
    xHi = widget.ranges[0].lo
    for ci in range(self.minAvailCI,self.maxAvailCI+1):
      xLo = xHi
      xFracHi = (1 + ci - self.minAvailCI)/float(self.maxAvailCI + 1 - self.minAvailCI)
      xHi = widget.ranges[0].lo*(1.0 - xFracHi) + widget.ranges[0].hi*xFracHi

      ciFrac = (ci + 0.5 - self.minAvailCI)/(self.maxAvailCI + 1 - self.minAvailCI)
      red = self.hueGraphs[0].interpolate(ciFrac)
      grn = self.hueGraphs[1].interpolate(ciFrac)
      blu = self.hueGraphs[2].interpolate(ciFrac)
      pgplot.pgscr(ci, red, grn, blu)

      widget.gui.plotter.lowLevelPlotter.setColour(ci)
      widget.gui.plotter.lowLevelPlotter.drawRectangle(xLo, yLo, xHi, yHi)

    widget.gui.plotter.lowLevelPlotter.setFill(oldFill)
    widget.gui.plotter.lowLevelPlotter.setColour(oldColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawAll(self, gui):
#*** could maybe also set the min ciFrac and hueFrac distances (used for point selection purposes) to suit the canvas dimensions?
    for hueI in range(self._numHues):
      widget = gui._widgetDict[self._hueNames[hueI]]
      self._redrawHueGraph(hueI, widget)

    widget = gui._widgetDict['colourbar']
    self._redrawColourBar(widget)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _canvasXYToCH(self, hueI, widget, clickEvent):
    (x, y) = clickEvent.getCursorXY()
    ciFrac  = (x - widget.ranges[0].lo)/(widget.ranges[0].hi - widget.ranges[0].lo)
    ciFrac  = max(0.0, min(1.0, ciFrac))
    hueFrac = (y - widget.ranges[1].lo)/(widget.ranges[1].hi - widget.ranges[1].lo)
    hueFrac = max(0.0, min(1.0, hueFrac))

    return (ciFrac, hueFrac)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _chToElements(self, hueI, chTuple):
    """
Find the point with the closest CH position to the one given, and find the point with next highest CI. If the former distance falls below a cutoff, return the elementI in closeElementI, and return nextHighestElementI=None; otherwise set closeElementI=None and return nextHighestElementI. 
    """

    (x0,y0) = chTuple
    x0 = max(0.0,min(1.0,x0))
    nextHighestElementI = None # default
    for i in range(self.hueGraphs[hueI]._numPoints):
      (x,y) = self.hueGraphs[hueI][i]
      deltaX = (x - x0)/self._minCiFrac
      deltaY = (y - y0)/self._minHueFrac
      distSquared = deltaX*deltaX + deltaY*deltaY

      if distSquared<1.0:
        closeElementI = i
        nextHighestElementI = None
        break

      if nextHighestElementI is None and x>x0:
        nextHighestElementI = i # can't be 0

    else:
      # If we got here, means no close element was found.
      closeElementI = None
      if nextHighestElementI is None: # only possible here if x0==1.0.
        nextHighestElementI = self.hueGraphs[hueI]._numPoints - 1

    return (closeElementI, nextHighestElementI)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkUndoRedoEnabling(self, gui):
    undoButton = gui._widgetDict['undo']
    if self.actionHistory.numUndoableActions>0:
      undoButton.changeEnableState(True)
    else:
      undoButton.changeEnableState(False)

    redoButton = gui._widgetDict['redo']
    if self.actionHistory.numRedoableActions>0:
      redoButton.changeEnableState(True)
    else:
      redoButton.changeEnableState(False)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _changeButtonStatesWhileDragging(self, gui, amDragging):
    for btnStr in ['cancel','delete']:
      gui._widgetDict[btnStr].changeEnableState(amDragging)

    for btnStr in ['save','load']:
      gui._widgetDict[btnStr].changeEnableState(not amDragging)

    if amDragging:
      gui._widgetDict['undo'].changeEnableState(False)
      gui._widgetDict['redo'].changeEnableState(False)
    else:
      self._checkUndoRedoEnabling(gui)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _canvasCallback(self, hueI, widget, clickEvent):
    """
In general this routine has to accomplish the following things:
	- Make an appropriate change to self.hueGraphs[hueI].
	- Record that change in self.actionHistory
	- Redraw the hue graph.
	- Enable/disable the undo/redo buttons as appropriate.
	- Set/Unset clickEvent.showLine as appropriate.

One of the following actions may happen:
	* If clickEvent.showLine==True, it means we already clicked in the canvas and are dragging a point. We should set the (previously selected) point, then set clickEvent.showLine to False.

	* clickEvent.showLine==False and we are 'near' an existing point. Select the point and set clickEvent.showLine to True.

	* clickEvent.showLine==False and we are 'far' from an existing point. Insert a new point.
    """

    chTupleNew = self._canvasXYToCH(hueI, widget, clickEvent)
    tupleToErase = None # default

    newClickEvent = clickEvent.copy()

    if newClickEvent.showLine: # means we are dragging a point and have just clicked on the place where we want it dragged to.
      self._changeButtonStatesWhileDragging(widget.gui, False)

      if hueI==self.selectedHueI:
        chTupleOld = self.hueGraphs[hueI][self.selectedElementI]

        if self.selectedElementI==0 or self.selectedElementI==self.hueGraphs[hueI]._numPoints-1:
          if self.selectedElementI==0:
            chTupleNew = (0.0, chTupleNew[1])
          else:
            chTupleNew = (1.0, chTupleNew[1])

          tupleToErase = chTupleOld

        self.hueGraphs[hueI][self.selectedElementI] = chTupleNew
        action = ChangeAction(hueI, self.selectedElementI, chTupleOld, chTupleNew)
        self.actionHistory.append(action)

        newClickEvent.showLine = False

      else:
        # cancel it because we clicked in the wrong canvas.
        self.selectedHueI = None
        self.selectedElementI = None
        newClickEvent.showLine = False

        return newClickEvent

    else: # we are not dragging a pre-selected point.
      # Find out if we are close to an existing point.
      (closeElementI, nextHighestElementI) = self._chToElements(hueI, chTupleNew)
      if not closeElementI is None: # We are. Set up to drag this point.
        self.selectedHueI = hueI
        self.selectedElementI = closeElementI
        newClickEvent.showLine = True ### maybe also reset the csr x,y to the exact centre of the point?

        self._changeButtonStatesWhileDragging(widget.gui, True)

        return newClickEvent# no redraw of either the hue graph or colour bar.

      else: # We are not. Insert a new point.
        self.hueGraphs[hueI].insert(nextHighestElementI, chTupleNew)
        action = InsertAction(hueI, nextHighestElementI, chTupleNew)
        self.actionHistory.append(action)

    self._checkUndoRedoEnabling(widget.gui)

    # Display the altered graph+colourbar:
    self._redrawHueGraph(hueI, widget, tupleToErase)
    self._redrawColourBar(widget.gui._widgetDict['colourbar'])

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def redCanvasCallback(self, widget, clickEvent):
    return self._canvasCallback(0, widget, clickEvent)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def grnCanvasCallback(self, widget, clickEvent):
    return self._canvasCallback(1, widget, clickEvent)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def bluCanvasCallback(self, widget, clickEvent):
    return self._canvasCallback(2, widget, clickEvent)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def undoCallback(self, undoBtnWidget, clickEvent):
    action = self.actionHistory.getLast()

    if action.typeStr=='change':
      tupleToErase = action.chTupleNew
    else:
      tupleToErase = None

    self._undo(action)
    self._checkUndoRedoEnabling(undoBtnWidget.gui)

    # Display the altered graph+colourbar:
    hueGraphWidget = undoBtnWidget.gui._widgetDict[self._hueNames[action.hueI]]
    self._redrawHueGraph(action.hueI, hueGraphWidget, tupleToErase)
    self._redrawColourBar(undoBtnWidget.gui._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def redoCallback(self, redoBtnWidget, clickEvent):
    action = self.actionHistory.getNext()

    if action.typeStr=='change':
      tupleToErase = action.chTupleOld
    else:
      tupleToErase = None

    self._redo(action)
    self._checkUndoRedoEnabling(redoBtnWidget.gui)

    # Display the altered graph+colourbar:
    hueGraphWidget = redoBtnWidget.gui._widgetDict[self._hueNames[action.hueI]]
    self._redrawHueGraph(action.hueI, hueGraphWidget, tupleToErase)
    self._redrawColourBar(redoBtnWidget.gui._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def cancelCallback(self, canBtnWidget, clickEvent):
    # This button should be enabled only after a hue/element has been selected by a mouse click near a symbol in the appropriate hue canvas. Basically it just unselects the hue/element, returns to default cursor mode and disables the 'delete' and 'cancel' buttons.

    self.selectedHueI = None
    self.selectedElementI = None
    canBtnWidget.changeEnableState(False)
    canBtnWidget.gui._widgetDict['delete'].changeEnableState(False)

    clickEvent.showLine = False

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def deleteCallback(self, delBtnWidget, clickEvent):
    chTupleOld = self.hueGraphs[self.selectedHueI][self.selectedElementI]

    # Perform the action:
    self.hueGraphs[self.selectedHueI].delete(self.selectedElementI)

    # Record the action:
    action = DeleteAction(self.selectedHueI, self.selectedElementI, chTupleOld)
    self.actionHistory.append(action)

    # Display the altered graph+colourbar:
    hueGraphWidget = delBtnWidget.gui._widgetDict[self._hueNames[self.selectedHueI]]
    self._redrawHueGraph(self.selectedHueI, hueGraphWidget)
    self._redrawColourBar(delBtnWidget.gui._widgetDict['colourbar'])

    # Activate the 'cancel' callback, which will disable and re-plot both 'delete' and 'cancel' buttons.
    canBtnWidget = delBtnWidget.gui._widgetDict['cancel']
    return self.cancelCallback(canBtnWidget, clickEvent)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _gotEqExp(self, gotStr, expStr, fh):
    if gotStr==expStr:
      return True
    else:
      print 'Expected %s got %s' % (expStr, gotStr)
      fh.close()
      return False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _loadMap(self, fileName):
    success = False # default

    tempHueGraphs = []

    fh = open(fileName, 'r')
    for hueI in range(self._numHues):
      hueStr = self._hueNames[hueI]
      hue = self.hueGraphs[hueI]

      line = fh.readline()
      [gotStr, gotHueStr] = line[:-1].split('=') #**** should test first that there are 2 fields
      if not self._gotEqExp(gotStr, 'hue', fh): return False
      if not self._gotEqExp(gotHueStr, hueStr, fh): return False

      line = fh.readline()
      [gotStr, firstStr] = line[:-1].split('=') #**** should test first that there are 2 fields
      if not self._gotEqExp(gotStr, 'first', fh): return False
      first = float(firstStr)

      line = fh.readline()
      [gotStr, lastStr] = line[:-1].split('=') #**** should test first that there are 2 fields
      if not self._gotEqExp(gotStr, 'last', fh): return False
      last = float(lastStr)

      tempHueGraphs.append(HueGraph(first, last))

      line = fh.readline()
      [gotStr, numStr] = line[:-1].split('=') #**** should test first that there are 2 fields
      if not self._gotEqExp(gotStr, 'num', fh): return False
      numInternalHues = int(numStr)

      for i in range(numInternalHues):
        line = fh.readline()
        fields = line[:-1].split(' ')
        if len(fields)!=2:
          print 'Expected 2 space-separated float fields but the line is %s' % (line[:-1])
          fh.close()
          return False

        cf = float(fields[0])
        hf = float(fields[1])
        tempHueGraphs[hueI].insert(i+1, (cf, hf))

    fh.close()

    self.hueGraphs = []
    for hueI in range(self._numHues):
      self.hueGraphs.append(tempHueGraphs[hueI])

    return True

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def loadCallback(self, loadButtonWidget, clickEvent):
    fileName = raw_input("Load colourmap from file:")
    if not os.path.isfile(fileName):
      print 'Could not find a file %s' % (fileName)
      return clickEvent

    if not self._loadMap(fileName):
      print 'Could not load the colourmap.'
      return clickEvent

    # Wipe the action history:
    self.actionHistory = ActionHistory() # in a way it would be nice if we could store (and thus reload) the action history too.

    self._checkUndoRedoEnabling(loadButtonWidget.gui)

    # Display the altered graph+colourbar:
    for hueI in range(self._numHues):
      hueGraphWidget = loadButtonWidget.gui._widgetDict[self._hueNames[hueI]]
      self._redrawHueGraph(hueI, hueGraphWidget)
    self._redrawColourBar(loadButtonWidget.gui._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _saveMap(self, fileName):
    fh = open(fileName, 'w')
    for hueI in range(self._numHues):
      hueStr = self._hueNames[hueI]
      hue = self.hueGraphs[hueI]

      fh.write('hue=%s\n' % (hueStr))
      fh.write('first=%f\n' % (hue._firstH))
      fh.write('last=%f\n'  % (hue._lastH))
      numInternalHues = len(hue._internalList)
      fh.write('num=%d\n'  % (numInternalHues))
      for i in range(numInternalHues):
        fh.write('%f %f\n'  % (hue._internalList[i][0], hue._internalList[i][1]))

    fh.close()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def saveCallback(self, saveButtonWidget, clickEvent):
    fileName = raw_input("Save colourmap to file:")
    self._saveMap(fileName)
    print 'Saved.'
    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def defaultCallback(self, frameWidget, clickEvent):
    newClickEvent = clickEvent.copy()

    if newClickEvent.showLine: # means we are dragging a point and have just clicked on the place where we want it dragged to.
      self._changeButtonStatesWhileDragging(frameWidget.gui, False)

      # cancel it because we clicked outside the canvas.
      self.selectedHueI = None
      self.selectedElementI = None
      newClickEvent.showLine = False

    return newClickEvent

#.......................................................................
class ModifiedLowLevelPlotter(pgi.PgplotInterface):
  def __init__(self):
    pgi.PgplotInterface.__init__(self)###, pgi.ClickHandler())

    self.colours = {}
    self.maxCI = None
    self.addColour('black', 0.0, 0.0, 0.0)
    self.addColour('white', 1.0, 1.0, 1.0)

    # Let draw_widgets.Plotter add the rest of the necessary colours.

#.......................................................................



colourMap = ColourMap()

def exitFn(widgetObj, clickEvent):
  widgetObj.gui.plotter.cursorHandler.exitWasChosen = True
  return clickEvent

myPlotter = drw.Plotter(lowLevelPlotter=ModifiedLowLevelPlotter())

# Now set up the tree of widget objects:

sizes = [widgets.Size('exact', 10.0),widgets.Size('exact', 8.0)]
gui = widgets.GUI('Colour map GUI', sizes, myPlotter, childSequenceDir=0, defaultCallbackFunction=colourMap.defaultCallback, userInitialFunction=colourMap.initialize)#, debug=True)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
f0 = widgets.Frame(gui, 'f0', sizes, isTransparent=True, isEnabled=True\
    , bgColour=None, disabledBgColour=None, innerBufferFrac=None, outerBufferFrac=None\
    , childSequenceDir=1, alongJustify='spread', crossJustify='centre')

sizes = [widgets.Size('expandToFit', None),widgets.Size('exact', 0.5)]
colourBar = widgets.Canvas(f0, 'colourbar', sizes, callbackFunction=None, redrawOnClick=False\
    , bgColour='black', outerBufferFrac=None, initialDrawFunction=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
cRed = widgets.Canvas(f0, 'red', sizes, callbackFunction=colourMap.redCanvasCallback, redrawOnClick=False\
    , bgColour='black', outerBufferFrac=None, initialDrawFunction=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
cGrn = widgets.Canvas(f0, 'grn', sizes, callbackFunction=colourMap.grnCanvasCallback, redrawOnClick=False\
    , bgColour='black', outerBufferFrac=None, initialDrawFunction=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
cBlu = widgets.Canvas(f0, 'blu', sizes, callbackFunction=colourMap.bluCanvasCallback, redrawOnClick=False\
    , bgColour='black', outerBufferFrac=None, initialDrawFunction=None)


sizes = [widgets.Size('exact', 3.0),widgets.Size('expandToFit', None)]
f1 = widgets.Frame(gui, 'f1', sizes, isTransparent=True, isEnabled=True\
    , bgColour=None, disabledBgColour=None, innerBufferFrac=None, outerBufferFrac=None\
    , childSequenceDir=1, alongJustify='spread', crossJustify='centre')

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bExit = widgets.Button(f1, 'exit', sizes, 'Exit', callbackFunction=exitFn, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bLoad = widgets.Button(f1, 'load', sizes, 'Load', callbackFunction=colourMap.loadCallback, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bSave = widgets.Button(f1, 'save', sizes, 'Save', callbackFunction=colourMap.saveCallback, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bUndo = widgets.Button(f1, 'undo', sizes, 'Undo', callbackFunction=colourMap.undoCallback, isEnabled=False\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bRedo = widgets.Button(f1, 'redo', sizes, 'Redo', callbackFunction=colourMap.redoCallback, isEnabled=False\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bDelete = widgets.Button(f1, 'delete', sizes, 'Delete', callbackFunction=colourMap.deleteCallback, isEnabled=False\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

sizes = [widgets.Size('expandToFit', None),widgets.Size('expandToFit', None)]
bCancel = widgets.Button(f1, 'cancel', sizes, 'Cancel', callbackFunction=colourMap.cancelCallback, isEnabled=False\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None)

# Finally, get set everything in motion - construct the GUI, await user input (mouse clicks), then act on it.
#
gui()

