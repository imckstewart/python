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
This enables loading, alteration and saving of RGB colourmaps for pgplot via a GUI interface.

You'll see 3 broad black panels, stacked one over the other, and a narrow colour bar under all. Each of the 3 broad panels is associated with a hue - red, green, blue, ordered from bottom up. Each panel defines an amplitude function for its hue. The default function starts at 0 and ends at 1, with a linear rise between these two points. By use of the mouse, the user can either add more points for each curve (via a single mouse click anywhere in the panel sufficiently far from existing points) or drag an existing point (by a single click near that point, then a second click to where you want it to be moved). Note that the end points can also be dragged (although only vertically). An incipient drag can also be cancelled by making the second click on the 'cancel' button.

Points (except the end points) can be deleted, and actions can be undone or redone, via use of the appropriate buttons. A colourmap may be written or read via use of the 'save' or 'load' buttons.
"""

_module_name = 'pg_colourmap'

import os
import numpy as nu
import ppgplot as pgplot

import pgplot_interface as pgi
import widgeometry as wge
import draw_widgets as drw
import widgets
import colourmap as cm


#.......................................................................
class ColourMapCallbacks:
  # used for point selection purposes:
  _minCiFrac  = 0.02
  _minHueFrac = 0.02

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, colourMap=None):
    if colourMap is None:
      self.cm = cm.ColourMap()
    else:
      self.cm = colourMap

    self.selectedHueI = None # valid when clickEvent.showLine==True
    self.selectedElementI = None # valid when clickEvent.showLine==True

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
    self.worldXLo = gui.sizes[0].range.lo
    self.worldXHi = gui.sizes[0].range.hi
    self.worldYLo = gui.sizes[1].range.lo
    self.worldYHi = gui.sizes[1].range.hi
    self.xDeltaRatio = (self.vpXHi - self.vpXLo)/(self.worldXHi - self.worldXLo)
    self.yDeltaRatio = (self.vpYHi - self.vpYLo)/(self.worldYHi - self.worldYLo)

    self.drawAll(gui)

    gui.plotter.lowLevelPlotter.setColour('white')

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _redrawHueGraph(self, hueI, widget, tupleToErase=None):
    oldFill = widget.rootWidget.plotter.lowLevelPlotter.getFill()
    oldColour = widget.rootWidget.plotter.lowLevelPlotter.getColour()

    if not tupleToErase is None:
      # Draw the start and end points in the frame bkg colour before drawing all points and lines in white:
      colour = widget.parent.widgetPlotter.bgColour
      widget.rootWidget.plotter.lowLevelPlotter.setColour(colour)
      xs = nu.array([tupleToErase[0]])
      ys = nu.array([tupleToErase[1]])
      xs = widget.sizes[0].range.lo*(1.0 - xs) + widget.sizes[0].range.hi*xs
      ys = widget.sizes[1].range.lo*(1.0 - ys) + widget.sizes[1].range.hi*ys
      pgplot.pgpt(xs, ys, 0) # point type 0 is squares.

    # Draw the canvas background:
    widget.widgetPlotter.draw()

    # Now draw the points and lines:
    widget.rootWidget.plotter.lowLevelPlotter.setColour('white')
    (xs,ys) = self.cm.hueGraphs[hueI].unpackValues()
    xs = widget.sizes[0].range.lo*(1.0 - xs) + widget.sizes[0].range.hi*xs
    ys = widget.sizes[1].range.lo*(1.0 - ys) + widget.sizes[1].range.hi*ys
    pgplot.pgline(xs, ys)
    pgplot.pgpt(xs, ys, 0) # point type 0 is squares.

    widget.rootWidget.plotter.lowLevelPlotter.setFill(oldFill)
    widget.rootWidget.plotter.lowLevelPlotter.setColour(oldColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _redrawColourBar(self, widget):
    oldFill = widget.rootWidget.plotter.lowLevelPlotter.getFill()
    oldColour = widget.rootWidget.plotter.lowLevelPlotter.getColour()

    widget.rootWidget.plotter.lowLevelPlotter.setFill(True)
    yLo = widget.sizes[1].range.lo
    yHi = widget.sizes[1].range.hi
    xHi = widget.sizes[0].range.lo
    for ci in range(self.minAvailCI,self.maxAvailCI+1):
      xLo = xHi
      xFracHi = (1 + ci - self.minAvailCI)/float(self.maxAvailCI + 1 - self.minAvailCI)
      xHi = widget.sizes[0].range.lo*(1.0 - xFracHi) + widget.sizes[0].range.hi*xFracHi

      ciFrac = (ci + 0.5 - self.minAvailCI)/(self.maxAvailCI + 1 - self.minAvailCI)
      red = self.cm.hueGraphs[0].interpolate(ciFrac)
      grn = self.cm.hueGraphs[1].interpolate(ciFrac)
      blu = self.cm.hueGraphs[2].interpolate(ciFrac)
      pgplot.pgscr(ci, red, grn, blu)

      widget.rootWidget.plotter.lowLevelPlotter.setColour(ci)
      widget.rootWidget.plotter.lowLevelPlotter.drawRectangle(xLo, yLo, xHi, yHi)

    widget.rootWidget.plotter.lowLevelPlotter.setFill(oldFill)
    widget.rootWidget.plotter.lowLevelPlotter.setColour(oldColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawAll(self, gui):
#*** could maybe also set the min ciFrac and hueFrac distances (used for point selection purposes) to suit the canvas dimensions?
    for hueI in range(self.cm._numHues):
      widget = gui._widgetDict[self.cm._hueNames[hueI]]
      self._redrawHueGraph(hueI, widget)

    widget = gui._widgetDict['colourbar']
    self._redrawColourBar(widget)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _canvasXYToCH(self, hueI, widget, clickEvent):
    (x, y) = clickEvent.getCursorXY()
    ciFrac  = (x - widget.sizes[0].range.lo)/(widget.sizes[0].range.hi - widget.sizes[0].range.lo)
    ciFrac  = max(0.0, min(1.0, ciFrac))
    hueFrac = (y - widget.sizes[1].range.lo)/(widget.sizes[1].range.hi - widget.sizes[1].range.lo)
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
    for i in range(self.cm.hueGraphs[hueI]._numPoints):
      (x,y) = self.cm.hueGraphs[hueI][i]
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
        nextHighestElementI = self.cm.hueGraphs[hueI]._numPoints - 1

    return (closeElementI, nextHighestElementI)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkUndoRedoEnabling(self, gui):
    undoButton = gui._widgetDict['undo']
    if self.cm.actionHistory.numUndoableActions>0:
      undoButton.changeEnableState(True)
    else:
      undoButton.changeEnableState(False)

    redoButton = gui._widgetDict['redo']
    if self.cm.actionHistory.numRedoableActions>0:
      redoButton.changeEnableState(True)
    else:
      redoButton.changeEnableState(False)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _changeButtonStatesWhileDragging(self, gui, amDragging, pointIsDeletable=True):
    for btnStr in ['cancel']:
      gui._widgetDict[btnStr].changeEnableState(amDragging)

    if amDragging and pointIsDeletable:
      gui._widgetDict['delete'].changeEnableState(True)
    else:
      gui._widgetDict['delete'].changeEnableState(False)

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
	- Make an appropriate change to self.cm.hueGraphs[hueI].
	- Record that change in self.cm.actionHistory
	- Redraw the hue graph.
	- Enable/disable the undo/redo buttons as appropriate.
	- Set/Unset clickEvent.showLine as appropriate.

One of the following actions may happen:
	* If clickEvent.showLine==True, it means we already clicked in the canvas and are dragging a point. We should set the (previously selected) point, then set clickEvent.showLine to False.

	* clickEvent.showLine==False and we are 'near' an existing point. Select the point and set clickEvent.showLine to True.

	* clickEvent.showLine==False and we are 'far' from an existing point. Insert a new point.
    """

    newClickEvent = clickEvent.copy()

    chTupleNew = self._canvasXYToCH(hueI, widget, clickEvent)
    tupleToErase = None # default

    if newClickEvent.showLine: # means we are dragging a point and have just clicked on the place where we want it dragged to.
      self._changeButtonStatesWhileDragging(widget.rootWidget, False)

      if hueI==self.selectedHueI:
        chTupleOld = self.cm.hueGraphs[hueI][self.selectedElementI]

        if self.selectedElementI==0 or self.selectedElementI==self.cm.hueGraphs[hueI]._numPoints-1:
          if self.selectedElementI==0:
            chTupleNew = (0.0, chTupleNew[1])
          else:
            chTupleNew = (1.0, chTupleNew[1])

          tupleToErase = chTupleOld

        self.cm.hueGraphs[hueI][self.selectedElementI] = chTupleNew
        action = cm.ChangeAction(hueI, self.selectedElementI, chTupleOld, chTupleNew)
        self.cm.actionHistory.append(action)

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

        if closeElementI>0 and closeElementI<self.cm.hueGraphs[hueI]._numPoints-1:
          pointIsDeletable = True
        else:
          pointIsDeletable = False # cannot delete first or last points.

        self._changeButtonStatesWhileDragging(widget.rootWidget, True, pointIsDeletable)

        return newClickEvent# no redraw of either the hue graph or colour bar.

      else: # We are not. Insert a new point.
        self.cm.hueGraphs[hueI].insert(nextHighestElementI, chTupleNew)
        action = cm.InsertAction(hueI, nextHighestElementI, chTupleNew)
        self.cm.actionHistory.append(action)

    self._checkUndoRedoEnabling(widget.rootWidget)

    # Display the altered graph+colourbar:
    self._redrawHueGraph(hueI, widget, tupleToErase)
    self._redrawColourBar(widget.rootWidget._widgetDict['colourbar'])

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
    action = self.cm.actionHistory.getLast()

    if action.typeStr=='change':
      tupleToErase = action.chTupleNew
    else:
      tupleToErase = None

    self.cm._undo(action)
    self._checkUndoRedoEnabling(undoBtnWidget.rootWidget)

    # Display the altered graph+colourbar:
    hueGraphWidget = undoBtnWidget.rootWidget._widgetDict[self.cm._hueNames[action.hueI]]
    self._redrawHueGraph(action.hueI, hueGraphWidget, tupleToErase)
    self._redrawColourBar(undoBtnWidget.rootWidget._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def redoCallback(self, redoBtnWidget, clickEvent):
    action = self.cm.actionHistory.getNext()

    if action.typeStr=='change':
      tupleToErase = action.chTupleOld
    else:
      tupleToErase = None

    self.cm._redo(action)
    self._checkUndoRedoEnabling(redoBtnWidget.rootWidget)

    # Display the altered graph+colourbar:
    hueGraphWidget = redoBtnWidget.rootWidget._widgetDict[self.cm._hueNames[action.hueI]]
    self._redrawHueGraph(action.hueI, hueGraphWidget, tupleToErase)
    self._redrawColourBar(redoBtnWidget.rootWidget._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def cancelCallback(self, canBtnWidget, clickEvent):
    # This button should be enabled only after a hue/element has been selected by a mouse click near a symbol in the appropriate hue canvas. Basically it just unselects the hue/element, returns to default cursor mode and disables the 'delete' and 'cancel' buttons.

    newClickEvent = clickEvent.copy()

    self._changeButtonStatesWhileDragging(canBtnWidget.rootWidget, False)

    self.selectedHueI = None
    self.selectedElementI = None
    newClickEvent.showLine = False

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def deleteCallback(self, delBtnWidget, clickEvent):
    chTupleOld = self.cm.hueGraphs[self.selectedHueI][self.selectedElementI]

    # Perform the action:
    self.cm.hueGraphs[self.selectedHueI].delete(self.selectedElementI)

    # Record the action:
    action = cm.DeleteAction(self.selectedHueI, self.selectedElementI, chTupleOld)
    self.cm.actionHistory.append(action)

    # Display the altered graph+colourbar:
    hueGraphWidget = delBtnWidget.rootWidget._widgetDict[self.cm._hueNames[self.selectedHueI]]
    self._redrawHueGraph(self.selectedHueI, hueGraphWidget)
    self._redrawColourBar(delBtnWidget.rootWidget._widgetDict['colourbar'])

    # Activate the 'cancel' callback, which will disable and re-plot both 'delete' and 'cancel' buttons.
    canBtnWidget = delBtnWidget.rootWidget._widgetDict['cancel']
    return self.cancelCallback(canBtnWidget, clickEvent)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def loadCallback(self, loadButtonWidget, clickEvent):
    fileName = raw_input("Load colourmap from file:")
    if not os.path.isfile(fileName):
      print 'Could not find a file %s' % (fileName)
      return clickEvent

    if not self.cm._loadMap(fileName):
      print 'Could not load the colourmap.'
      return clickEvent

    # Wipe the action history:
    self.cm.actionHistory = cm.ActionHistory() # in a way it would be nice if we could store (and thus reload) the action history too.

    self._checkUndoRedoEnabling(loadButtonWidget.rootWidget)

    # Display the altered graph+colourbar:
    for hueI in range(self.cm._numHues):
      hueGraphWidget = loadButtonWidget.rootWidget._widgetDict[self.cm._hueNames[hueI]]
      self._redrawHueGraph(hueI, hueGraphWidget)
    self._redrawColourBar(loadButtonWidget.rootWidget._widgetDict['colourbar'])

    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def saveCallback(self, saveButtonWidget, clickEvent):
    fileName = raw_input("Save colourmap to file:")
    self.cm._saveMap(fileName)
    print 'Saved.'
    return clickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def defaultCallback(self, frameWidget, clickEvent):
    newClickEvent = clickEvent.copy()

    if newClickEvent.showLine: # means we are dragging a point and have just clicked on the place where we want it dragged to.
      self._changeButtonStatesWhileDragging(frameWidget.rootWidget, False)

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



colourMap = ColourMapCallbacks()

myPlotter = drw.Plotter(lowLevelPlotter=ModifiedLowLevelPlotter())

# Now set up the tree of widget objects:

sizeSpecs = [widgets.Size('exact', 10.0),widgets.Size('exact', 8.0)]
gui = widgets.GUI('Colour map GUI', sizeSpecs, myPlotter\
  , childSequenceDir=widgets.HORIZONTAL\
  , defaultCallbackFunction=colourMap.defaultCallback\
  , userInitialFunction=colourMap.initialize)#, debug=True)

sizeSpecs = [widgets.Size('expandToFit', childrenJustify='centre')\
           , widgets.Size('expandToFit', childrenJustify='spread')]
f0 = widgets.Frame(gui, 'f0', sizeSpecs, isTransparent=True\
  , isEnabled=True, bgColour=None, disabledBgColour=None\
  , childSequenceDir=widgets.VERTICAL\
  )

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('exact', 0.5)]
colourBar = widgets.Canvas(f0, 'colourbar', sizeSpecs\
  , callbackFunction=None, redrawOnClick=False, bgColour='black'\
  , initialDrawFunction=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
cRed = widgets.Canvas(f0, 'red', sizeSpecs\
  , callbackFunction=colourMap.redCanvasCallback, redrawOnClick=False\
  , bgColour='black', initialDrawFunction=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
cGrn = widgets.Canvas(f0, 'grn', sizeSpecs\
  , callbackFunction=colourMap.grnCanvasCallback, redrawOnClick=False\
  , bgColour='black', initialDrawFunction=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
cBlu = widgets.Canvas(f0, 'blu', sizeSpecs\
  , callbackFunction=colourMap.bluCanvasCallback, redrawOnClick=False\
  , bgColour='black', initialDrawFunction=None)


sizeSpecs = [widgets.Size('exact', 3.0, childrenJustify='centre')\
           , widgets.Size('expandToFit', childrenJustify='spread')]
f1 = widgets.Frame(gui, 'f1', sizeSpecs, isTransparent=True\
  , isEnabled=True, bgColour=None, disabledBgColour=None\
  , childSequenceDir=widgets.VERTICAL)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bExit = widgets.Button(f1, 'exit', sizeSpecs, 'Exit'\
  , callbackFunction=widgets.defaultExitFn, isEnabled=True\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bLoad = widgets.Button(f1, 'load', sizeSpecs, 'Load'\
  , callbackFunction=colourMap.loadCallback, isEnabled=True\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bSave = widgets.Button(f1, 'save', sizeSpecs, 'Save'\
  , callbackFunction=colourMap.saveCallback, isEnabled=True\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bUndo = widgets.Button(f1, 'undo', sizeSpecs, 'Undo'\
  , callbackFunction=colourMap.undoCallback, isEnabled=False\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bRedo = widgets.Button(f1, 'redo', sizeSpecs, 'Redo'\
  , callbackFunction=colourMap.redoCallback, isEnabled=False\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bDelete = widgets.Button(f1, 'delete', sizeSpecs, 'Delete'\
  , callbackFunction=colourMap.deleteCallback, isEnabled=False\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

sizeSpecs = [widgets.Size('expandToFit'),widgets.Size('expandToFit')]
bCancel = widgets.Button(f1, 'cancel', sizeSpecs, 'Cancel'\
  , callbackFunction=colourMap.cancelCallback, isEnabled=False\
  , bgColour=None, disabledBgColour=None, inkColour=None\
  , disabledInkColour=None)

# Finally, get set everything in motion - construct the GUI, await user input (mouse clicks), then act on it.
#
gui()

