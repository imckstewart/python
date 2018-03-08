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

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, cursorHandler=None):

    if cursorHandler is None:
      self.cursorHandler = ClickHandler()
    else:
      self.cursorHandler = cursorHandler

    self.deviceName = None
    self.widthInches    = None
    self.yOnXRatio      = None

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

    self.plotDeviceIsOpened = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def initializePlot(self, worldXLo, worldXHi, worldYLo, worldYHi\
    , deviceName=None, widthInches=None, yOnXRatio=1.0, doPad=True, fixAspect=True):

    if deviceName is None:
      self.deviceName = self._defaultDeviceName
    else:
      self.deviceName = deviceName

    if doPad:
      (worldXLo, worldXHi, worldYLo, worldYHi) = plu.doPadLimits(worldXLo, worldXHi, worldYLo, worldYHi)

    self.doPad = doPad
    self.fixAspect = fixAspect
    self.worldXLo = worldXLo
    self.worldXHi = worldXHi
    self.worldYLo = worldYLo
    self.worldYHi = worldYHi

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

    pgplot.pgsvp(0.0,0.999,0.0,0.999)
    if fixAspect:
      pgplot.pgwnad(worldXLo, worldXHi, worldYLo, worldYHi)
    else:
      pgplot.pgswin(worldXLo, worldXHi, worldYLo, worldYHi)
    pgplot.pgsfs(2)

    pgplot.pgslw(1)
    pgplot.pgsch(self._charHeight)

    self._setColourRepresentations()

    (xLoPixels, xHiPixels, yLoPixels, yHiPixels) = pgplot.pgqvsz(3)
    (xLoInches, xHiInches, yLoInches, yHiInches) = pgplot.pgqvsz(1)
    self.xPixelWorld = (xHiInches - xLoInches) / (xHiPixels - xLoPixels)
    self.yPixelWorld = (yHiInches - yLoInches) / (yHiPixels - yLoPixels)

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

    (x0,x1,y0,y1) = pgplot.pgqvsz(3)
    pixelXSizeWorld = (self.worldXHi - self.worldXLo)/(x1 - x0)
    pixelYSizeWorld = (self.worldYHi - self.worldYLo)/(y1 - y0)
    return (pixelXSizeWorld, pixelYSizeWorld)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _setColourRepresentations(self):
    if not self.plotDeviceIsOpened:
      raise ValueError('you must open a device before you can set colour representations.')

    for colour in self.colours.keys():
      ci = self.colours[colour]['ci']
      rgb = self.colours[colour]['rgb']
      if not rgb is None:
        pgplot.pgscr(ci, rgb[0], rgb[1], rgb[2])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def addColour(self, colour, red, grn, blu):
    rgb = [red, grn, blu]
    if colour in self.colours.keys():
      self.colours[colour]['rgb'] = rgb
    else:
      if self.maxCI is None:
        self.maxCI = 0
      else:
        self.maxCI += 1
##### check it does not exceed max.
      self.colours[colour] = {'ci':self.maxCI,'rgb':rgb}

    if self.plotDeviceIsOpened:
      ci = self.colours[colour]['ci']
      pgplot.pgscr(ci, rgb[0], rgb[1], rgb[2])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def isColourNameValid(self, colour):
    if colour in self.colours.keys():
      return True
    else:
      return False

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
  def terminatePlot(self, withBox=False):
    if not self.plotDeviceIsOpened:
      raise ValueError("You have not yet opened a PGPLOT device.")

    if withBox:
      xOpt = 'BC'#NT'
      yOpt = 'BC'#NT'
      pgplot.pgsci(1)
      pgplot.pgbox(xOpt, 0.0, 0, yOpt, 0.0, 0)
    pgplot.pgend()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':
  pass













