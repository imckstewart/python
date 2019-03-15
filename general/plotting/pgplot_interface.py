#!/usr/bin/env python
#
# Name:                         pgplot_interface
#
# NOTE!! To make use of this module, you not only have to download and
# build the ppgplot module (note the two p's), which doesn't come with
# the normal python dist; you also have to have pgplot installed, and
# pointed to by the envar PGPLOT_DIR.
#
# Author: Ian Stewart
#
# TODO:
#
#    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#    Copyright (C) 2014  Ian M Stewart
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

_module_name = 'pgplot_interface'

"""
This is intended to provide a common interface for routines such as those in plot_wire_frame.py and draw_widgets.py.
"""

import numpy as nu
import ppgplot as pgplot

import my_exceptions as ex
import plot_utils as plu
import pg_defs as pgd


#.......................................................................
class ClickEvent:
  def __init__(self, xOfClick=0.0, yOfClick=0.0, showLine=False):
    self.xOfClick = xOfClick
    self.yOfClick = yOfClick
    self.showLine = showLine

  def getCursorXY(self):
    return (self.xOfClick, self.yOfClick)

  def copy(self):
    return ClickEvent(self.xOfClick, self.yOfClick, self.showLine)

#.......................................................................
class ClickHandler:
  def __init__(self, initialClickEvent=None, lineMode=2):
    if initialClickEvent is None:
      self.initialClickEvent = ClickEvent()
    else:
      self.initialClickEvent = initialClickEvent

    self.lineMode = lineMode
    self.exitWasChosen = False

  def __call__(self, clickEvent):
    if clickEvent is None:
      lastClickEvent = self.initialClickEvent
    else:
      lastClickEvent = clickEvent

    # Note that 'char' will have value 'A', 'D' or 'X' depending on whether the left, centre or right mouse buttons respectively were clicked.
    if lastClickEvent.showLine:
      (xOfClick, yOfClick, char) = pgplot.pgband(self.lineMode, 0, lastClickEvent.xOfClick, lastClickEvent.yOfClick)
    else:
      (xOfClick, yOfClick, char) = pgplot.pgcurs(lastClickEvent.xOfClick, lastClickEvent.yOfClick)

    newClickEvent = ClickEvent(xOfClick, yOfClick, lastClickEvent.showLine)
    return newClickEvent


#.......................................................................
class PgplotInterface:
  _defaultDeviceName = '/xs'
  _charHeight = 1.0
  _defaultPointStyle = pgd.P_POINT

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, cursorHandler=None):

    if cursorHandler is None:
      self.cursorHandler = ClickHandler()
    else:
      self.cursorHandler = cursorHandler

    self.deviceName  = None
    self.widthInches = None
    self.yOnXRatio   = None

    self.doPad = None
    self.fixAspect = None
    self.worldXLo = None
    self.worldXHi = None
    self.worldYLo = None
    self.worldYHi = None

    # These are the default colour mappings:
    self.colours =  {\
        'black':{'ci': 1,'rgb':None}\
    ,   'white':{'ci': 0,'rgb':None}\
    ,     'red':{'ci': 2,'rgb':None}\
    ,   'green':{'ci': 3,'rgb':None}\
    ,    'blue':{'ci': 4,'rgb':None}\
    ,    'cyan':{'ci': 5,'rgb':None}\
    , 'magenta':{'ci': 6,'rgb':None}\
    ,  'yellow':{'ci': 7,'rgb':None}\
    ,  'orange':{'ci': 8,'rgb':None}\
    ,  'lgreen':{'ci': 9,'rgb':None}\
    ,  'green1':{'ci':10,'rgb':None}\
    ,   'lblue':{'ci':11,'rgb':None}\
    ,  'purple':{'ci':12,'rgb':None}\
    ,    'rose':{'ci':13,'rgb':None}\
    ,    'grey':{'ci':14,'rgb':None}\
    ,   'lgrey':{'ci':15,'rgb':None}}
    self.maxCI = None
    for colour in self.colours.keys():
      ci = self.colours[colour]['ci']
      if self.maxCI is None or ci > self.maxCI:
        self.maxCI = ci

    self._oldCI            = None
    self._oldLineStyle     = None
    self._oldLineThickness = None
    self._oldFillStyle     = None
    self._oldCharHeight    = None
    self.pointStyle = self._defaultPointStyle

    self.plotDeviceIsOpened = False # default

    self.previousColours = []

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def initializePlot(self, worldXLo, worldXHi, worldYLo, worldYHi\
    , deviceName=None, widthInches=None, yOnXRatio=1.0, doPad=True, fixAspect=False\
    , xLabel=None, yLabel=None, title='', startPlotter=True):
    # It is handy to have this separate method since on the one hand I prefer to pass around an instance rather than a class, and on the other it can be useful to postpone loading all the attributes.

    if self.plotDeviceIsOpened:
      raise ValueError("You cannot call initializePlot() after you have opened a PGPLOT device.")

    self.worldXLo = worldXLo
    self.worldXHi = worldXHi
    self.worldYLo = worldYLo
    self.worldYHi = worldYHi

    if deviceName is None:
      self.deviceName = self._defaultDeviceName
    else:
      self.deviceName = deviceName

    self.widthInches = widthInches
    self.yOnXRatio   = yOnXRatio
    self.doPad = doPad
    self.fixAspect = fixAspect
    self.yLabel = yLabel
    self.title  = title

    if xLabel is None and yLabel is None and title=='':
      self._drawBox = False
    else:
      self._drawBox = True

    self._vXHi = 0.999

    if xLabel is None:
      self.xLabel = ''
      self._vXLo = 0.0
      self._xAxisOptions = 'BC'
    else:
      self.xLabel = xLabel
      self._vXLo = 0.1
      self._xAxisOptions = 'BCNT'

    if yLabel is None:
      self.yLabel = ''
      self._vYLo = 0.0
      self._yAxisOptions = 'BC'
    else:
      self.yLabel = yLabel
      self._vYLo = 0.1
      self._yAxisOptions = 'BCNT'

    if title=='':
      self._vYHi = 0.999
    else:
      self._vYHi = 0.9

    if self.doPad:
      (self.worldXLo, self.worldXHi, self.worldYLo, self.worldYHi)\
        = plu.doPadLimits(self.worldXLo, self.worldXHi, self.worldYLo, self.worldYHi)

    if startPlotter:
      self.startPlotter()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def addColour(self, colour, red, grn, blu):
    if self.plotDeviceIsOpened:
      raise ValueError("You cannot call addColour() after you have opened a PGPLOT device.")

    rgb = [red, grn, blu]
    if colour in self.colours.keys():
      self.colours[colour]['rgb'] = rgb
    else:
      if self.maxCI is None:
        self.maxCI = 0
      else:
        self.maxCI += 1
      self.colours[colour] = {'ci':self.maxCI,'rgb':rgb}

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def isColourNameValid(self, colour):
    if colour in self.colours.keys():
      return True
    else:
      return False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def startPlotter(self):
    if self.plotDeviceIsOpened:
      raise ValueError("You already started a plot!")

    devId = pgplot.pgopen(self.deviceName)
    self.plotDeviceIsOpened = True

    if not self.widthInches is None:
      pgplot.pgpap(self.widthInches, self.yOnXRatio)

    # For devices /xs, /xw, /png etc, should make the paper white and the ink black. Only for /ps does pgplot default to that.
    #
    deviceWithoutFile = self.deviceName.split('/')[-1]
    if deviceWithoutFile=='xs' or deviceWithoutFile=='xw' or deviceWithoutFile=='png':
      pgplot.pgscr(0,1.0,1.0,1.0)
      pgplot.pgscr(1,0.0,0.0,0.0)

    pgplot.pgsvp(self._vXLo, self._vXHi, self._vYLo, self._vYHi)

    if self.fixAspect:
      pgplot.pgwnad(self.worldXLo, self.worldXHi, self.worldYLo, self.worldYHi)
    else:
      pgplot.pgswin(self.worldXLo, self.worldXHi, self.worldYLo, self.worldYHi)
    pgplot.pgsfs(2)

    pgplot.pgslw(1)
    pgplot.pgsch(self._charHeight)

    self._setColourRepresentations()

    # Set up things so calling pgplot.pggray() won't overwrite the CR of any of the colours in self.colours.
    #
    (minCI,maxCI) = pgplot.pgqcir()
    if minCI<=self.maxCI:
      pgplot.pgscir(self.maxCI+1,maxCI)

    (xLoPixels, xHiPixels, yLoPixels, yHiPixels) = pgplot.pgqvsz(3)
    (xLoInches, xHiInches, yLoInches, yHiInches) = pgplot.pgqvsz(1)
    self.xPixelWorld = (xHiInches - xLoInches) / (xHiPixels - xLoPixels)
    self.yPixelWorld = (yHiInches - yLoInches) / (yHiPixels - yLoPixels)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def xFracToWorld(self, xFrac):
    return self.worldXLo*(1.0 - xFrac) + self.worldXHi*xFrac

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def yFracToWorld(self, yFrac):
    return self.worldYLo*(1.0 - yFrac) + self.worldYHi*yFrac

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getColourIndexRange(self):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    (minCI,maxCI) = pgplot.pgqcol()
    minCI = max(minCI, len(self.colours.keys()))
    return (minCI, maxCI)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getPixelSize(self):
    # This returns a tuple giving the X and Y dimensions of the device pixels in world coordinates.

    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    return (self.xPixelWorld, self.yPixelWorld)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _setColourRepresentations(self):
    if not self.plotDeviceIsOpened:
      raise ValueError('you must open a device before you can set colour representations.')

##### check the number of colours does not exceed max for the device.

    for colour in self.colours.keys():
      ci = self.colours[colour]['ci']
      rgb = self.colours[colour]['rgb']
      if not rgb is None:
        pgplot.pgscr(ci, rgb[0], rgb[1], rgb[2])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setColour(self, colour):
    if colour in self.colours.keys():
      ci = self.colours[colour]['ci']
      pgplot.pgsci(ci)
    else:
      try:
        ci = colour
        pgplot.pgsci(ci)
      except:
        raise ex.UnrecognizedChoiceObject(colour)

    self.previousColours.append(ci)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def undoSetColour(self):
    try:
      ci = self.previousColours.pop()
    except IndexError:
      ci = None

    if not ci is None:
      pgplot.pgsci(ci)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getColour(self):
    return pgplot.pgqci()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setFill(self, doFill=True):
    if doFill:
      pgplot.pgsfs(1)
    else:
      pgplot.pgsfs(2)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getFill(self):
    fillStyle = pgplot.pgqfs()
    if fillStyle==1:
      return True
    else:
      return False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPoint(self, x, y, pointStyle=None):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    if pointStyle is None:
      localPointStyle = self.pointStyle
    else:
      localPointStyle = pointStyle

    xs = nu.array([x])
    ys = nu.array([y])
    pgplot.pgpt(xs, ys, localPointStyle)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPoints(self, xs, ys, pointStyle=None):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    if pointStyle is None:
      localPointStyle = self.pointStyle
    else:
      localPointStyle = pointStyle

    pgplot.pgpt(xs, ys, localPointStyle)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawErrorBars(self, xs, ys, yUncs, pointStyle=None):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    if pointStyle is None:
      localPointStyle = self.pointStyle
    else:
      localPointStyle = pointStyle

    pgplot.pgpt(xs, ys, localPointStyle)
    yLos = ys - yUncs
    yHis = ys + yUncs
    for i in range(len(xs)):
      self.drawLine(xs[i], yLos[i], xs[i], yHis[i])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawLine(self, xLo, yLo, xHi, yHi):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    pgplot.pgmove(xLo, yLo)
    pgplot.pgdraw(xHi, yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawRectangle(self, xLo, yLo, xHi, yHi):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    pgplot.pgrect(xLo, xHi, yLo, yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPolyLine(self, xs, ys):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    pgplot.pgline(xs, ys)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPolygon(self, polygonXs, polygonYs):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    pgplot.pgpoly(polygonXs, polygonYs)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def writeCenteredText(self, x, y, text):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    pgplot.pgptxt(x, y, 0.0, 0.5, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawLegend(self, listOfStyles, listOfColours, listOfTexts, fracHeight=0.25, isLeft=True, isUp=True):
    # if style is None just draw a line segment.
    numTexts = len(listOfTexts)
    x0 = self.xFracToWorld(0.02)
    x1 = self.xFracToWorld(0.025)
    x2 = self.xFracToWorld(0.03)
    for i in range(numTexts):
      yFrac = 1.0 - fracHeight*((numTexts - i - 0.5)/float(numTexts))
      y = self.yFracToWorld(yFrac)
      self.setColour(listOfColours[i])
      if listOfStyles[i] is None:
        self.drawLine(x0, y, x1, y)
      else:
        self.drawPoint(0.5*(x0+x1), y, listOfStyles[i])
      pgplot.pgsci(1)
      pgplot.pgptxt(x2, y, 0.0, 0.0, listOfTexts[i])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def terminatePlot(self):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    if self._drawBox:
      pgplot.pgsci(1)
      pgplot.pgbox(self._xAxisOptions, 0.0, 0, self._yAxisOptions, 0.0, 0)
      pgplot.pglab(self.xLabel, self.yLabel, self.title)

    pgplot.pgend()

    self.plotDeviceIsOpened = False

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':

  import numpy as nu

  import pg_defs as pgd

  worldXLo = 0.0
  worldXHi = 1.0
  worldYLo = 0.0
  worldYHi = 1.0

  xs = nu.array([0.11, 0.16, 0.43, 0.59, 0.64, 0.82])
  ys = nu.sqrt(xs)

  plotter = PgplotInterface()
  plotter.initializePlot(worldXLo, worldXHi, worldYLo, worldYHi, xLabel='X of frogs', yLabel='Y of frogs', title='Frog distribution')
  plotter.setColour('green')
  plotter.drawPoints(xs, ys, pgd.P_CIRCLE)
  plotter.terminatePlot()










