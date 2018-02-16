#!/usr/bin/env python

# Name:                         draw_widgets
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
This module forms an intermediate layer between the top layer module 'widgets.py' and a bottom-layer module which performs the heavy lifting work of drawing the widgets. I found it convenient to construct this middle layer since the actual drawing package one wants to use may vary.

What we have here is a set of classes, one per widget, the function of each of which is to draw that widget. These are all sub-classes of _WidgetPlotter, but none of them are intended to be instantiated directly, but rather by calling factory functions from within the class Plotter. As well as the factory functions, Plotter also provides the methods, plus the attribute 'cursorHandler', required by the various classes in widgets.py. Consult the header of that module for a detailed description.

Class Plotter takes two arguments at instantiation, each of which may be left at defaults. The first is an object 'lowLevelPlotter' which must have the following attributes and methods:

	cursorHandler	# this will be copied to the Plotter instance, just to avoid confusing the poor widgets.py user by the introduction of another class.
	addColour(self, colourStr, redFloat, grnFloat, bluFloat)
	initializePlot(self, xLo, xHi, yLo, yHi, widthInches, yOnXRatio, doPadBool, fixAspectBool)
	isColourNameValid(self, colourStr)	# returns a boolean
	setFill(self, setFillBool)
	setColour(self, colourStr)
	drawRectangle(self, xLo, yLo, xHi, yHi)
	drawLine(self, xLo, yLo, xHi, yHi)
	drawPolygon(self, xNumpyVec, yNumpyVec)
	writeCenteredText(self, textCentreX, textCentreY, textStr)
	getPixelSize(self)			# returns a tuple of 2 floats.
	terminatePlot(self, withBoxBool)

If the user does not supply their own 'lowLevelPlotter' instance the Plotter class will try to use the class pgplot_interface.PgplotInterface.

Note that 'cursorHandler' has no direct use in the present module. It's interface requirements are described in the header of widgets.py and an example implementation is the class pgplot_interface.ClickHandler.

The second instantiation argument of class Plotter is 'colourRGBDict', which should be a dictionary, each key of which is a colour name, the value being a list of three floats, each of value between 0 and 1 inclusive, which represent the amounts of red, green and blue respectively in that colour. An example of this form is the class attribute _WidgetPlotter._defaultColourRGBDict.
"""

_module_name = 'draw_widgets'

import math

import misc_utils as mu

importPgiWentOk = False # default
try:
  import pgplot_interface as pgi
  importPgiWentOk = True
except:
  pass


#.......................................................................
class _WidgetPlotter:
  _defaultColourRGBDict = {\
         'shadow':[0.0,0.0,0.0]\
    ,       'lit':[1.0,1.0,1.0]\
    ,'halfshadow':[0.55,0.55,0.55]\
    ,   'halflit':[0.75,0.75,0.75]\
    ,     'paper':[0.65,0.65,0.65]\
    ,       'ink':[1.0,1.0,1.0]\
    ,  'half-ink':[0.8,0.8,0.8]\
    ,     'black':[0.0,0.0,0.0]\
    ,     'white':[1.0,1.0,1.0]\
    ,       'red':[1.0,0.0,0.0]\
    ,   'halfred':[0.75,0.5,0.5]}

  _defaultBgColour = 'paper'
  _defaultInkColour = 'red'
  _defaultDisabledInkColour = 'halfred'

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, text, bgColour, disabledBgColour, inkColour, disabledInkColour):
    self.lowLevelPlotter = lowLevelPlotter
    self.xLo = xLo
    self.xHi = xHi
    self.yLo = yLo
    self.yHi = yHi
    self.text = text

    if bgColour is None:
      self.bgColour = self._defaultBgColour
    else:
      self.bgColour = bgColour

    if disabledBgColour is None:
      self.disabledBgColour = self.bgColour
    else:
      self.disabledBgColour = disabledBgColour

    if inkColour is None:
      self.inkColour = self._defaultInkColour
    else:
      self.inkColour = inkColour

    if disabledInkColour is None:
      self.disabledInkColour = self._defaultDisabledInkColour
    else:
      self.disabledInkColour = disabledInkColour

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _drawBackground(self, bgColour):
    self.lowLevelPlotter.setFill(True)
    self.lowLevelPlotter.setColour(bgColour)
    self.lowLevelPlotter.drawRectangle(self.xLo, self.yLo, self.xHi, self.yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, enabled):
    if enabled:
      bgColour = self.bgColour
      inkColour = self.inkColour
      litColour = 'lit'
      shadowColour = 'shadow'
    else:
      bgColour = self.disabledBgColour
      inkColour = self.disabledInkColour
      litColour = 'halflit'
      shadowColour = 'halfshadow'

    self._drawBackground(bgColour)

    return (inkColour, litColour, shadowColour)

#.......................................................................
class _FramePlotter(_WidgetPlotter):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, bgColour\
    , disabledBgColour, drawGroove):

    _WidgetPlotter.__init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi\
      , '', bgColour, disabledBgColour, None, None)

    self.drawGroove = drawGroove # Draw a groove at the frame border; otherwise draw a ridge. 
    (self.pixelXSize, self.pixelYSize) = self.lowLevelPlotter.getPixelSize()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, enabled):
    (inkColour, litColour, shadowColour) = _WidgetPlotter.draw(self, enabled)

    self.lowLevelPlotter.setFill(False)

    if self.drawGroove:
      self.lowLevelPlotter.setColour(shadowColour)
    else:
      self.lowLevelPlotter.setColour(litColour)

    x0 = self.xLo
    x1 = self.xHi - self.pixelXSize
    y0 = self.yLo + self.pixelYSize
    y1 = self.yHi
    self.lowLevelPlotter.drawRectangle(x0, y0, x1, y1)

    if self.drawGroove:
      self.lowLevelPlotter.setColour(litColour)
    else:
      self.lowLevelPlotter.setColour(shadowColour)

    x0 = self.xLo
    x1 = self.xHi
    y0 = self.yLo
    y1 = self.yHi
    self.lowLevelPlotter.drawLine(x0, y0, x1, y0)
    self.lowLevelPlotter.drawLine(x1, y0, x1, y1)
    x0 = self.xLo + self.pixelXSize
    x1 = self.xHi - self.pixelXSize*2.0
    y0 = self.yLo + self.pixelYSize*2.0
    y1 = self.yHi - self.pixelYSize
    self.lowLevelPlotter.drawLine(x0, y0, x0, y1)
    self.lowLevelPlotter.drawLine(x0, y1, x1, y1)

#.......................................................................
class _LabelPlotter(_WidgetPlotter):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, text, bgColour\
    , disabledBgColour, inkColour, disabledInkColour):

    _WidgetPlotter.__init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi\
      , text, bgColour, disabledBgColour, inkColour, disabledInkColour)

    self.textCentreX = 0.5*(xLo+xHi)
    self.textCentreY = 0.5*(yLo+yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, enabled):
    (inkColour, litColour, shadowColour) = _WidgetPlotter.draw(self, enabled)

    self.lowLevelPlotter.setColour(inkColour)
    self.lowLevelPlotter.writeCenteredText(self.textCentreX, self.textCentreY\
      , self.text)

#.......................................................................
class _ButtonPlotter(_WidgetPlotter):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, text, bgColour\
    , disabledBgColour, inkColour, disabledInkColour):

    _WidgetPlotter.__init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi\
      , text, bgColour, disabledBgColour, inkColour, disabledInkColour)

    self.textCentreX = 0.5*(xLo+xHi)
    self.textCentreY = 0.5*(yLo+yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _drawButton(self, inkColour, topLeftColour, botRightColour):
    self.lowLevelPlotter.setColour(inkColour)
    self.lowLevelPlotter.writeCenteredText(self.textCentreX, self.textCentreY\
      , self.text)

    self.lowLevelPlotter.setColour(topLeftColour)
    self.lowLevelPlotter.drawLine(self.xLo, self.yLo, self.xLo, self.yHi)
    self.lowLevelPlotter.drawLine(self.xLo, self.yHi, self.xHi, self.yHi)

    self.lowLevelPlotter.setColour(botRightColour)
    self.lowLevelPlotter.drawLine(self.xLo, self.yLo, self.xHi, self.yLo)
    self.lowLevelPlotter.drawLine(self.xHi, self.yLo, self.xHi, self.yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, enabled, isPressed):
    (inkColour, litColour, shadowColour) = _WidgetPlotter.draw(self, enabled)
    if isPressed:
      self._drawButton(inkColour, shadowColour, litColour)
    else:
      self._drawButton(inkColour, litColour, shadowColour)

#.......................................................................
class _CanvasPlotter(_WidgetPlotter):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, bgColour):

    _WidgetPlotter.__init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi\
      , '', bgColour, None, None, None)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    self._drawBackground(self.bgColour)

#.......................................................................
class _NoTransform:
  # Eventually subclass it from a generic transform object.
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def posFracToValue(self, positionFraction):
    return positionFraction

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def valueToPosFrac(self, value):
    return value

#.......................................................................
class _SliderPlotter(_WidgetPlotter):
  """
This draws a slider widget. The rectangular field of the slider is divided (along its short dimension) into two fields, one for the scale, the other for the slider itself. The scale need only be drawn once at the start-up of the GUI but the slider will need to be redrawn each time the slider moves.

The slider itself comprises a groove and a pointer.

Note that 'nor' is short for normal to the long dimension, 'par' short for parallel to the long dimension.
  """

  numGrooveEndPoints = 7 # should be at least 2
  sliderFieldNorWidthFrac = 0.5
  grooveNorCentreFrac = 0.25
  grooveParStartFrac = 0.05
  grooveNorHalfWidthFrac = 0.1

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi, isVertical\
    , transformObject, bgColour, disabledBgColour, inkColour, disabledInkColour):

    _WidgetPlotter.__init__(self, lowLevelPlotter, xLo, xHi, yLo, yHi\
      , '', bgColour, disabledBgColour, inkColour, disabledInkColour)

    self.isVertical = isVertical # direction of long dimension.
    if transformObject is None:
      self.transformObject = _NoTransform()
    else:
      self.transformObject = transformObject

    if isVertical:
      self.sliderFieldXLo = xLo
      self.sliderFieldXHi = xLo + (xHi - xLo)*self.sliderFieldNorWidthFrac
      self.sliderFieldYLo = yLo
      self.sliderFieldYHi = yHi
      grooveParCushion = (yHi - yLo)*self.grooveParStartFrac
      self.grooveParStart = yLo + grooveParCushion
      self.grooveParFinis = yHi - grooveParCushion
      self.grooveNorCentre = xLo + (xHi - xLo)*self.grooveNorCentreFrac
      self.grooveNorHalfWidth = self.grooveNorHalfWidthFrac*(xHi - xLo)
    else:
      self.sliderFieldYLo = yLo
      self.sliderFieldYHi = yLo + (yHi - yLo)*self.sliderFieldNorWidthFrac
      self.sliderFieldXLo = xLo
      self.sliderFieldXHi = xHi
      grooveParCushion = (xHi - xLo)*self.grooveParStartFrac
      self.grooveParStart = xLo + grooveParCushion
      self.grooveParFinis = xHi - grooveParCushion
      self.grooveNorCentre = yLo + (yHi - yLo)*self.grooveNorCentreFrac
      self.grooveNorHalfWidth = self.grooveNorHalfWidthFrac*(yHi - yLo)

    self.grooveParLen = self.grooveParFinis - self.grooveParStart

##### error if self.ptrTrackLen <= 0.

    self.groovePoly = nu.zeros([self.numGrooveEndPoints*2,2],nu.float)

    if self.isVertical:
      norI = 0 # i.e. the slider-normal direction is X
      parI = 1 # i.e. the slider-parallel direction is Y
    else:
      norI = 1 # i.e. the slider-normal direction is Y
      parI = 0 # i.e. the slider-parallel direction is X

    # Store all the positions for the groove polygon:
    #
    centreNor = self.grooveNorCentre
    centrePar = self.grooveParStart
    i = 0

    self.groovePoly[i,parI] = centrePar
    self.groovePoly[i,norI] = centreNor - self.grooveNorHalfWidth
    i += 1

    for j in range(1,self.numGrooveEndPoints-1):
      angle = mu.fracVal(0.0, math.pi, j/float(self.numGrooveEndPoints-1))
      self.groovePoly[i,parI] = centrePar - self.grooveNorHalfWidth*math.sin(angle)
      self.groovePoly[i,norI] = centreNor - self.grooveNorHalfWidth*math.cos(angle)
      i += 1

    self.groovePoly[i,parI] = centrePar
    self.groovePoly[i,norI] = centreNor + self.grooveNorHalfWidth
    i += 1

    centrePar = self.grooveParFinis

    self.groovePoly[i,parI] = centrePar
    self.groovePoly[i,norI] = centreNor + self.grooveNorHalfWidth
    i += 1

    for j in range(1,self.numGrooveEndPoints-1):
      angle = mu.fracVal(0.0, math.pi, j/float(self.numGrooveEndPoints-1))
      self.groovePoly[i,parI] = centrePar + self.grooveNorHalfWidth*math.sin(angle)
      self.groovePoly[i,norI] = centreNor + self.grooveNorHalfWidth*math.cos(angle)
      i += 1

    self.groovePoly[i,parI] = centrePar
    self.groovePoly[i,norI] = centreNor - self.grooveNorHalfWidth

    # Store all the (zero-offset) positions for the pointer polygon:
    #
    self.pointerPoly = nu.zeros([3,2],nu.float)
    self.pointerPoly[0,parI] =  0.0
    self.pointerPoly[0,norI] =  self.grooveNorHalfWidth * 3.0
    self.pointerPoly[1,parI] = -self.grooveNorHalfWidth * 1.5
    self.pointerPoly[1,norI] =  0.0
    self.pointerPoly[2,parI] =  self.grooveNorHalfWidth * 1.5
    self.pointerPoly[2,norI] =  0.0

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getPosFracFromCursor(self, x, y):
    """
Returns the fraction position of the cursor from 0 to 1 along the pointer track.
    """
    if self.isVertical:
      posFracOnTrack = (y - self.grooveParStart)/self.grooveParLen
    else:
      posFracOnTrack = (x - self.grooveParStart)/self.grooveParLen

    posFracOnTrack = min(1.0, max(0.0, posFracOnTrack))

    return posFracOnTrack

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getPointerLoc(self, posFracOnTrack):
    """
Returns the world coordinate location of the pointer.
    """
    if self.isVertical:
      ptrX = self.grooveNorCentre
      ptrY = self.grooveParStart + posFracOnTrack*self.grooveParLen
    else:
      ptrX = self.grooveParStart + posFracOnTrack*self.grooveParLen
      ptrY = self.grooveNorCentre

    return (ptrX, ptrY)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getValue(self, x, y):
    posFracOnTrack = self.getPosFracFromCursor(x, y)
    return self.transformObject.posFracToValue(posFracOnTrack)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _drawScale(self, inkColour):
    pass
###

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _drawGroove(self, inkColour):
    self.lowLevelPlotter.setFill(True)
    self.lowLevelPlotter.setColour(inkColour)
    self.lowLevelPlotter.drawPolygon(self.groovePoly[:,0], self.groovePoly[:,1])

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _drawPtr(self, ptrX, ptrY, inkColour):
    self.lowLevelPlotter.setFill(True)
    self.lowLevelPlotter.setColour(self.bgColour)
    self.lowLevelPlotter.drawPolygon(self.pointerPoly[:,0]+ptrX, self.pointerPoly[:,1]+ptrY)

    self.lowLevelPlotter.setFill(False)
    self.lowLevelPlotter.setColour(inkColour)
    self.lowLevelPlotter.drawPolygon(self.pointerPoly[:,0]+ptrX, self.pointerPoly[:,1]+ptrY)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, enabled, x, y):
    posFracOnTrack = self.getPosFracFromCursor(x, y)
    (ptrX, ptrY) = self.getPointerLoc(posFracOnTrack)

    (inkColour, litColour, shadowColour) = _WidgetPlotter.draw(self, enabled)

    self._drawScale(inkColour)

    self.lowLevelPlotter.setFill(True)
    self.lowLevelPlotter.setColour(self.bgColour)
    self.lowLevelPlotter.drawRectangle(self.sliderFieldXLo, self.sliderFieldYLo, self.sliderFieldXHi, self.sliderFieldYHi)

    self._drawGroove(inkColour)
    self._drawPtr(ptrX, ptrY, inkColour)


#.......................................................................
# This is the only class an external user should instantiate.
#.......................................................................
class Plotter:
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, lowLevelPlotter=None, colourRGBDict={}):

    if lowLevelPlotter is None:
      if not importPgiWentOk:
        raise ImportError('Module for default lowLevelPlotter object did not import.')
      else:
        self.lowLevelPlotter = pgi.PgplotInterface()
    else:
      self.lowLevelPlotter = lowLevelPlotter

    self.cursorHandler = self.lowLevelPlotter.cursorHandler

    for colour in _WidgetPlotter._defaultColourRGBDict.keys():
      red = _WidgetPlotter._defaultColourRGBDict[colour][0]
      grn = _WidgetPlotter._defaultColourRGBDict[colour][1]
      blu = _WidgetPlotter._defaultColourRGBDict[colour][2]
      self.lowLevelPlotter.addColour(colour, red, grn, blu)

    for colour in colourRGBDict.keys():
      red = colourRGBDict[colour][0]
      grn = colourRGBDict[colour][1]
      blu = colourRGBDict[colour][2]
      self.lowLevelPlotter.addColour(colour, red, grn, blu)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def initializePlot(self, xLo, xHi, yLo, yHi, bgColour):
    widthInches = xHi - xLo
    yOnXRatio = (yHi - yLo)/widthInches
    self.lowLevelPlotter.initializePlot(xLo, xHi, yLo, yHi\
      , widthInches=widthInches, yOnXRatio=yOnXRatio, doPad=False, fixAspect=True)

    if bgColour is None:
      localBgColour = _WidgetPlotter._defaultBgColour
    else:
      localBgColour = bgColour

    self.lowLevelPlotter.setFill(True)
    self.lowLevelPlotter.setColour(localBgColour)
    self.lowLevelPlotter.drawRectangle(xLo, yLo, xHi, yHi)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def checkColour(self, colour):
    return self.lowLevelPlotter.isColourNameValid(colour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def terminatePlot(self):
    self.lowLevelPlotter.terminatePlot(withBox=False)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getFramePlotter(self, xLo, xHi, yLo, yHi, bgColour=None\
    , disabledBgColour=None, drawGroove=True):

    return _FramePlotter(self.lowLevelPlotter, xLo, xHi, yLo, yHi\
      , bgColour, disabledBgColour, drawGroove)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getLabelPlotter(self, xLo, xHi, yLo, yHi, text, bgColour=None\
    , disabledBgColour=None, inkColour=None, disabledInkColour=None):

    return _LabelPlotter(self.lowLevelPlotter, xLo, xHi, yLo, yHi\
      , bgColour, disabledBgColour, inkColour, disabledInkColour, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getButtonPlotter(self, xLo, xHi, yLo, yHi, text, bgColour=None\
    , disabledBgColour=None, inkColour=None, disabledInkColour=None):

    return _ButtonPlotter(self.lowLevelPlotter, xLo, xHi, yLo, yHi\
      , text, bgColour, disabledBgColour, inkColour, disabledInkColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getCanvasPlotter(self, xLo, xHi, yLo, yHi, bgColour=None):
    return _CanvasPlotter(self.lowLevelPlotter, xLo, xHi, yLo, yHi, bgColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def getSliderPlotter(self, xLo, xHi, yLo, yHi, transformObject, isVertical, bgColour=None\
    , disabledBgColour=None, inkColour=None, disabledInkColour=None):

    return _SliderPlotter(self.lowLevelPlotter, xLo, xHi, yLo, yHi\
      , isVertical, transformObject, bgColour, disabledBgColour, inkColour\
      , disabledInkColour)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':

  xLo = 0.0
  xHi = 5.0
  yLo = 0.0
  yHi = 4.0
  butXLo = 1.0
  butXHi = 3.5
  butYLo = 1.2
  butYHi = 2.7
  butText = 'Press here for frogs'

  plotter = Plotter()
  plotter.initializePlot(xLo, xHi, yLo, yHi, 'paper')

  fp0 = plotter.getFramePlotter(xLo, xHi, yLo, yHi)
  fp0.draw(True)

  fp1 = plotter.getFramePlotter(xLo+0.1, xHi-0.1, yLo+0.1, yHi-0.1)
  fp1.draw(True)

  bp0 = plotter.getButtonPlotter(butXLo, butXHi, butYLo, butYHi, butText)
  bp0.draw(enabled=True, isPressed=False)

  bp1 = plotter.getButtonPlotter(butXLo, butXHi, 0.3, 1.0, 'This is not text')
  bp1.draw(enabled=False, isPressed=False)

  bp2 = plotter.getButtonPlotter(3.8, 4.5, butYLo, butYHi, 'BLUB!')
  bp2.draw(enabled=True, isPressed=True)

  plotter.terminatePlot()















