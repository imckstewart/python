#!/usr/bin/env python

# Name:                         widgets
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
This module sets up classes to allow the construction of a tree of simple 'widgets'.

Widgets are conceived to be objects arranged in a tree. Each widget thus has a single parent, except the root widget, which has none. Each widget may have 0 or more children.

Note that, although it is assumed that widgets are rectangular (strictly speaking, orthotopes), spatially nested, and that each is to be associated with an image as part of a graphical user interface, the spatial extents and locations of each widget are taken care of by routines in module widgeometry, and the drawing of widgets is performed in module draw_widgets.

How to use the API:
===================
The first class to be instantiated must be 'GUI'. After that, other non-abstract classes (i.e. those whose names don't begin with an underscore) may be instantiated. Each of the non-GUI classes requires a parent, which must be either the GUI instance or an instance of class 'Frame'. Many of the widget types can be supplied with a callback function of the user's choice, which is called if the widget is selected (usually, it will be assumed, by clicking on it with the mouse). After all the widgets have been instantiated, the final step is to call the 'GUI' instance. A schematic for use of these classes is as follows:

  # Construct plotterObject

  sizeSpecs = [Size(<args>),Size(<args>)]
  mygui = GUI('demo gui', sizeSpecs, plotterObject)
  sizeSpecs = [Size(<args>),Size(<args>)]
  somewidget = <widget class>(gui, <name>, sizeSpecs, <etc>)
  . . .
  mygui()

For a more detailed example of how to use the widget classes, see the tests at the end of the present module .

Other objects required:
=======================
The present module assumes that each widget occupies a rectangular field, but the actual routines to draw the widgets have been abstracted to an object which should be passed to the GUI instance at initialization as argument 'plotter'. This object must have the following attributes and methods:

	cursorHandler
	initializePlot(xlo, xhi, ylo, yhi, bgColour)
	checkColour(colour)
	terminatePlot()
	getFramePlotter(xLo, xHi, yLo, yHi, bgColour, disabledBgColour, drawGroove)
	getLabelPlotter(xLo, xHi, yLo, yHi, text, bgColour, disabledBgColour, inkColour, disabledInkColour)
	getButtonPlotter(xLo, xHi, yLo, yHi, text, bgColour, disabledBgColour, inkColour, disabledInkColour)
	getCanvasPlotter(xLo, xHi, yLo, yHi, bgColour)
	getSliderPlotter(xLo, xHi, yLo, yHi, transformObject, isVertical, bgColour, disabledBgColour, inkColour, disabledInkColour)

If the user does not supply such an object, the module will attempt to access the Plotter class described in module draw_widgets. More detailed information on the 'plotter' object may be obtained by perusing that module.

The 'plotter' object involves other objects, described briefly as follows:

  * cursorHandler: the purpose of this is to obtain input from the user, which is mostly expected to consist of cursor placement and mouse clicks. It has very little direct exposure in the present module. It must be callable, and the expectation is that the call should block while waiting for a mouse click or other user input. It should also have a provision for the user to set a boolean attribute 'exitWasChosen', since a positive test of this flag is the only way for the call to the 'GUI' instance to exit nicely. The user may find it convenient to add further attributes and methods to the 'cursorHandler' object, either for purposes of handshaking with their callbacks, or to suit the 'plotter' object they supply. An example of a 'cursorHandler' class is given in pgplot_interface.ClickHandler.

A list of the required attributes and methods of this object is as follows:

	exitWasChosen			# boolean
	__call__(self, clickEvent)	# also returns a 'clickEvent' object. **NOTE** that a user-written cursorHandler must be able to create and store an initialized version of the clickEvent object in the case that the argument to this call is None.

  * clickEvent: this is an object designed to store information about cursor position and mouse clicks. It has little direct exposure in the present module, but it must have the following methods:

	getCursorXY(self)		# expected to return a tuple (x,y) of floats.
	copy(self)

See pgplot_interface.ClickEvent for an example class.

  * 'colour' objects: these are not directly accessed by the present module, they have meaning only for the plotter. In the draw_widgets.Plotter example class they are simply strings.

  * transformObject: this is designed for Slider objects which have non-linear scales. No attributes and methods of this objects are directly accessed by the present module; whatever 'transformObject' is supplied by the user to the instantiation of a Slider object is passed through to the factory function plotter.getSliderPlotter() described above.

  * The factory functions 'plotter.get<Widget>Plotter()' described above return respective objects as follows:

	- FramePlotter: must have method
		draw(self, enabled)

	- LabelPlotter: must have method
		draw(self, enabled)

	- ButtonPlotter: must have method
		draw(self, enabled, isPressed)

	- CanvasPlotter: must have method
		draw(self, redraw)

	- SliderPlotter: must have methods
		draw(self, enable, x, y)
		getValue(self, x, y)			# returns the (presumably floating-point) value of the slider from the cursor's (x,y) position.

Callback functions:
===================
Each 'active' widget may be given a callback function (CBF) at time of instantiation. The CBF is expected to take 2 arguments, the first being the widget 'self' object, the second being the ClickEvent object recognized by cursorHandler (see above for a description of this). The callbackFunction is expected to return another object of type ClickEvent, although None is also acceptable. See below for the result of a None return.

If the cursor position at time of mouse click falls within a Frame, but either not within any of the children, or the child it falls within returns None, then the Frame's default CBF is actuated. If the user supplied no default CBF for the Frame, the Frame also returns None to its own parent Frame.

User input:
===========
What happens when the user clicks somewhere inside the GUI window? There are three possibilities: one of the user's callback functions (CBFs) is activated, one of the user's empty-margin or default CBFs for Frame objects is activated, or the module's own 'do-nothing' CBF is activated. Which of these occurs depends on a complicated set of conditions which are best described via a flowchart, given below, which describes the decision tree as it effects a Frame object (which is the only widget which may physically enclose other 'child' widgets) and its children. The end result of this tree is the value returned to its parent by the Frame object.

	 ________________
	| Frame enabled? |<NO> --------------------> Frame returns result of do-nothing CBF.
	|________________|
	<YES>
	  |
	 _V___________________
	| Was the mouse click |
	| inside any child?   |<NO> ---------------> Frame returns result of its own default CBF.
	|_____________________|                 ^
	<YES>                                   |
	  |                                     |     -
	 _V_________________                    |      :
	| Is the child a    |                   |      :
	| _ClickableWidget? |<NO> ------------->|      :
	|___________________|                   |      :
	<YES>                                   |      :
	  |                                     |      :
	 _V_____________________                |      : - This all takes place inside the
	| Is the child enabled? |               |      :   doOnMouseClick() method of the child.
	|_______________________|               |      :
	<YES>                <NO>               |      :
	  |                    |                |      :
	 _V___________    _____V_________       |      :
	| Child calls |  | Child calls   |      |      :
	| its CBF.    |  | 'do-nothing'. |      |      :
	|_____________|  |_______________|      |      :
	            |      |                    |     -
	      ______V______V_______             |
	     | Is the result None? |<YES> ----->
	     |_____________________|
	     <NO>
	      |
	       ------------------------------------> Frame returns the child's result.
"""

_module_name = 'widgets'

import time

import my_exceptions as ex
import widgeometry as wge

importDrawWentOk = False # default
try:
  import draw_widgets as drw
  importDrawWentOk = True
except:
  pass

_dirStrs = ['X','Y']
HORIZONTAL = 0
VERTICAL   = 1

#.......................................................................
def defaultExitFn(widgetObj, clickEvent):
  widgetObj.rootWidget.plotter.cursorHandler.exitWasChosen = True
  return clickEvent

#.......................................................................
class Size(wge.WidgetSize):
  """
This subclasses wge.WidgetSize in order to define some minimum buffer distances.
  """
  _defaultOuterBuffer = wge.Buffer(0.01)
  _defaultInnerBuffer = wge.Buffer(0.01)
  def __init__(self, spaceDemand, maxExtent=None, outerBuffer=None\
    , innerBuffer=None, childrenJustify='spread'):

    if innerBuffer is None:
      localInnerBuffer = self._defaultInnerBuffer
    else:
      localInnerBuffer = innerBuffer

    if outerBuffer is None:
      localOuterBuffer = self._defaultOuterBuffer
    else:
      localOuterBuffer = outerBuffer

    wge.WidgetSize.__init__(self, spaceDemand, maxExtent, localOuterBuffer\
      , localInnerBuffer, childrenJustify)


#.......................................................................
class Children:
  """
This bundles together a list of 'child' _Widget objects with the axis along which they are to be arrayed.
  """
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, childList=[], childSequenceDir=0):
    self.childList = childList
    self.childSequenceDir = childSequenceDir

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __str__(self, spaces=''):
    myStr  = spaces+'< %s object.\n' % (self.__class__.__name__)
    myStr += spaces+'  seq dir = %d\n' % (self.childSequenceDir)
    if len(self.childList)<1:
      myStr += spaces+'  Zero children\n'
    else:
      myStr += spaces+'  Children:\n'
      for child in self.childList:
        myStr += spaces+'    %s\n' % (child.name)

    return myStr + spaces+'>'

#.......................................................................
class _TextWidget:
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, text):
    self.text = text

#.......................................................................
class _Widget:
  _numAxes = 2

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, isTransparent, isEnabled\
    , bgColour, disabledBgColour, inkColour, disabledInkColour\
    , childSequenceDir=None):
    # 'parent' must either be an instance of class Frame, or None.
    # 'sizeSpecs' must be a list with 2 elements (one for each axis), each being an instance of class wge.WidgetSize.

    self.parent = parent # Must be a Frame object or subclass thereof; or None if this widget is the outermost GUI window.
    if not parent is None and name in parent.rootWidget._widgetDict.keys():
      raise ValueError('Name %s is already taken by another widget.' % (name))

    self.name          = name
    self.sizes         = sizes
    if len(self.sizes)!=self._numAxes:
       raise ValueError("You need to provide %d elements in the list 'sizes', not %d" % (self._numAxes, len(self.sizes)))

    self.isTransparent = isTransparent

    if self.parent is None or self.parent.isEnabled:
      self.isEnabled = isEnabled
    else:
      self.isEnabled = False # we don't allow a child to be enabled if the parent is not.

    # These can be None; the plotting routines should be able to handle this.
    self.bgColour          = bgColour
    self.disabledBgColour  = disabledBgColour
    self.inkColour         = inkColour
    self.disabledInkColour = disabledInkColour

    if childSequenceDir is None:
      self.children = None
    else:
      self.children = Children([], childSequenceDir)

    if self.parent is None:
      self.rootWidget = self
    else:
      self.rootWidget = self.parent.rootWidget
      if self.parent.children is None: # not ideal - you should set up the parent widget to be a Frame by supplying it with a non-None childSequenceDir when instantiating.
        self.parent.children = Children([self])
      else:
        self.parent.children.childList.append(self)
      # These actually work as desired, i.e. the 'self' is an instance of Button, Frame or whatever, not of bare _Widget.

      self.parent.rootWidget._widgetDict[self.name] = self

    self._colours = [\
       {'BG':self.bgColour}\
      ,{'Disabled-BG':self.disabledBgColour}\
      ,{'FG':self.inkColour}\
      ,{'Disabled-FG':self.disabledInkColour}]

    # This is set when the gui is finally run, after the dependency tree is constructed.
    self.redraw = True # if False, just draw the things which will change with user action (e.g. mouse clicks)

    self.widgetPlotter = None

    self._debug=False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def contains(self, x, y):
    if self.sizes[0].range.contains(x) and self.sizes[1].range.contains(y):
      return True
    else:
      return False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def changeEnableState(self, isEnabled):
    # This is needed because some callbacks may want to toggle this state. Also we need a method particularly for Frame objects, so they can also disable all their children.
    self.isEnabled = isEnabled
    self.redraw = True
    self.draw()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    raise ex.EmptyMethod()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    self.widgetPlotter.draw(self.isEnabled)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    # A return value of None will cause the parent object (which at present must be a Frame) to call its default callback.
    raise ex.EmptyMethod()
    # the normal return is expected to be a clickEvent object.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _doNothingCallback(self, widget, lastClickEvent):
    return None

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def checkColoursChildren(self):
    for i in range(len(self._colours)):
      clrStr = self._colours[i].keys()[0]
      colour = self._colours[i][clrStr]

      if not colour is None and not self.rootWidget.plotter.checkColour(colour):
        raise ValueError('%s colour %s is not recognized by the plotter.' % (clrStr, colour))

    if self.children is None:
      return

    for child in self.children.childList:
      child.checkColoursChildren()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __str__(self, spaces=''):
    myStr  = spaces+'< %s object.\n' % (self.__class__.__name__)
    myStr += spaces+'  name = %s\n' % (self.name)
    if self.sizes[0].range is None:
      myStr += spaces+'  .xLo = None\n'
      myStr += spaces+'  .xHi = None\n'
    else:
      myStr += spaces+'  .xLo = %e\n' % (self.sizes[0].range.lo)
      myStr += spaces+'  .xHi = %e\n' % (self.sizes[0].range.hi)

    if self.sizes[1].range is None:
      myStr += spaces+'  .yLo = None\n'
      myStr += spaces+'  .yHi = None\n'
    else:
      myStr += spaces+'  .yLo = %e\n' % (self.sizes[1].range.lo)
      myStr += spaces+'  .yHi = %e\n' % (self.sizes[1].range.hi)

#### more work on this

    if not self.children is None:
      for child in self.children.childList:
        myStr += child.__str__(spaces+'  ')+'\n'

    return myStr + spaces+'>'

#.......................................................................
class _PassiveWidget(_Widget):
  # A _PassiveWidget object has no callback function.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, isTransparent, isEnabled\
    , bgColour, disabledBgColour, inkColour, disabledInkColour\
    , childSequenceDir=None):

    _Widget.__init__(self, parent, name, sizeSpecs, isTransparent, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour\
      , childSequenceDir)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    return None

#.......................................................................
class _ClickableWidget(_Widget):
  # A _ClickableWidget object has a callback function (although this can be None, in which case the default is used). I'm also assuming that such objects are non-transparent.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, callbackFunction, redrawOnClick\
    , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
    , childSequenceDir=None):

    # The 'callbackFunction' is expected to take 2 arguments, the first being the widget 'self' object, the second being a ClickEvent object (see module header for a description of this). The callbackFunction is expected to return another object of type ClickEvent, although None is also acceptable. A return of None will cause the parent object of the present widget (which at time of writing must be a Frame) to call its default callback.

    _Widget.__init__(self, parent, name, sizeSpecs, False, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour\
      , childSequenceDir)

    if callbackFunction is None:
      self.callbackFunction = self._doNothingCallback
    else:
      self.callbackFunction = callbackFunction

    self.redrawOnClick = redrawOnClick

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      if self.redrawOnClick:
        self.drawOnClick()
      newClickEvent = self.callbackFunction(self, oldClickEvent)
    else:
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawOnClick(self):
    raise ex.EmptyMethod()

#.......................................................................
# Now the actual non-abstract widgets:
#.......................................................................
class Frame(_PassiveWidget):
  """
A Frame object primarily is designed to contain other 'child' objects of type _Widget. Clicking on it outside any of its children is supposed to generate no action, but note that the user can supply a defaultCallbackFunction which is called in such circumstances.
  """

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, isTransparent=False, isEnabled=True\
    , bgColour=None, disabledBgColour=None, childSequenceDir=VERTICAL\
    , defaultCallbackFunction=None):

    if childSequenceDir is None:
      raise ValueError("Frame instantiation argument 'childSequenceDir' cannot be None.")

    _PassiveWidget.__init__(self, parent, name, sizeSpecs, isTransparent\
      , isEnabled, bgColour, disabledBgColour, None, None\
      , childSequenceDir)

    if not self.parent is None and defaultCallbackFunction is None:
      self.defaultCallbackFunction = self.parent.defaultCallbackFunction
    else:
      self.defaultCallbackFunction = defaultCallbackFunction

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      (x, y) = lastClickEvent.getCursorXY()

      # A Frame object is expected to have self.children != None.
      for child in self.children.childList:
        if child.contains(x, y):
          newClickEvent = child.doOnMouseClick(oldClickEvent)
          break

      else: # no child contained the cursor at the time of mouse click.
        newClickEvent = None

      if newClickEvent is None: # can happen if (i) the cursor was inside no child, (ii) the child was a passive widget, (iii) child._doNothingCallback() was activated and returned None.
        if not self.defaultCallbackFunction is None:
          newClickEvent = self.defaultCallbackFunction(self, oldClickEvent)

    else: # Frame is not enabled.
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def changeEnableState(self, isEnabled):
    # This is needed because some callbacks may want to toggle this state. Also we need a method particularly for Frame objects, so they can also disable all their children.
    self.isEnabled = isEnabled
    # A Frame object is expected to have self.children != None.
    for child in self.children.childList:
      child.changeEnableState(isEnabled)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.rootWidget.plotter.getFramePlotter(self.sizes[0].range.lo\
      , self.sizes[0].range.hi, self.sizes[1].range.lo, self.sizes[1].range.hi\
      , self.bgColour, self.disabledBgColour, drawGroove=True)

    if self.children is None:
      return

    for child in self.children.childList:
      child.setUpPlotter()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    if not self.isTransparent:
      self.widgetPlotter.draw(self.isEnabled)

    if self.children is None:
      return

    for child in self.children.childList:
      if self.rootWidget._debug: print 'About to draw child %s of %s' % (child.name, self.name)
      child.draw()


#.......................................................................
class Label(_PassiveWidget,_TextWidget):
  """
Does what it says on the box. This is a passive widget - clicking on it performs no action.
  """
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, text, isEnabled=True, bgColour=None\
    , disabledBgColour=None, inkColour=None, disabledInkColour=None):

    _PassiveWidget.__init__(self, parent, name, sizeSpecs, False\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
      , childSequenceDir=None)

    _TextWidget.__init__(self, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.rootWidget.plotter.getLabelPlotter(self.sizes[0].range.lo\
      , self.sizes[0].range.hi, self.sizes[1].range.lo, self.sizes[1].range.hi\
      , self.text, self.bgColour, self.disabledBgColour, self.inkColour\
      , self.disabledInkColour)


#.......................................................................
class Button(_ClickableWidget,_TextWidget):
  """
A Button defines a rectangular field which, when clicked, calls some user-supplied function.
  """
  _doTest=False
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, text, callbackFunction=None\
    , isEnabled=True, bgColour=None, disabledBgColour=None, inkColour=None\
    , disabledInkColour=None):

    _ClickableWidget.__init__(self, parent, name, sizeSpecs, callbackFunction, True\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
      , childSequenceDir=None)

    _TextWidget.__init__(self, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.rootWidget.plotter.getButtonPlotter(self.sizes[0].range.lo\
      , self.sizes[0].range.hi, self.sizes[1].range.lo, self.sizes[1].range.hi\
      , self.text, self.bgColour, self.disabledBgColour, self.inkColour\
      , self.disabledInkColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawOnClick(self):
    if self._doTest and self.name=='b4':
      print '>>>Entering widgets.Button.drawOnClick()'

    self.widgetPlotter.draw(self.isEnabled, isPressed=True)
    time.sleep(0.1)
    self.widgetPlotter.draw(self.isEnabled, isPressed=False)

    if self._doTest and self.name=='b4':
      print '<<< Leaving widgets.Button.drawOnClick()'

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    self.widgetPlotter.draw(self.isEnabled, isPressed=False)

#.......................................................................
class CheckButton(Button):
  """
A CheckButton is a Button with a memory. Clicking on it toggles its state between selected and not selected.
  """
  defaultCheckState = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, text, callbackFunction=None\
    , isEnabled=True, bgColour=None, disabledBgColour=None, inkColour=None\
    , disabledInkColour=None, startState=None):

    Button.__init__(self, parent, name, sizeSpecs, text, callbackFunction, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour)

    if startState is None:
      self.isSelected = self.defaultCheckState
    else:
      self.isSelected = startState

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      self.isSelected = not self.isSelected
      self.draw()
      newClickEvent = self.callbackFunction(self, oldClickEvent)
    else:
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    self.widgetPlotter.draw(self.isEnabled, self.isSelected)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawOnClick(self): # inherited from Button, but we don't need it.
    raise ex.EmptyMethod()

#.......................................................................
class RadioButtons(Frame):
  """
Radio buttons are a line of CheckButton objects, only 1 of which may be selected at any time.
  """

  defaultRadioI = 0
  _test = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, buttonTexts, callbackFunction=None\
    , isEnabled=True, bgColour=None, disabledBgColour=None, inkColour=None\
    , disabledInkColour=None, childSequenceDir=VERTICAL\
    , defaultCallbackFunction=None, startI=None):

    if self._test:
      bgColour = 'green'
      disabledBgColour = 'blue'

    Frame.__init__(self, parent, name, sizeSpecs, True, isEnabled\
      , bgColour, disabledBgColour, childSequenceDir, defaultCallbackFunction)

#***** would be better to supply individual CBF for the buttons, and use a variant of the Frame.doOnMouseClick() which detected which child was clicked and set self.selectedI from that; or maybe try to abstract the non-click stuff of Frame as a _Frame class... hmm maybe not. :-/ 

    if callbackFunction is None:
      self.callbackFunction = self._doNothingCallback
    else:
      self.callbackFunction = callbackFunction

    self.inkColour = inkColour
    self.disabledInkColour = disabledInkColour

    if startI is None:
      self.selectedI = self.defaultRadioI
    else:
      self.selectedI = startI

    numButtons = len(buttonTexts)
    self.selectedI = max(0, min(numButtons-1, self.selectedI))

    for i in range(numButtons):
      text = buttonTexts[i]

      if i==self.selectedI:
        startState = True
      else:
        startState = False

      if self.name is None:
        childName = None
      else:
        childName = '%s_%d' % (self.name, i)

      childSizes = [wge.WidgetSize('expandToFit')\
                  , wge.WidgetSize('expandToFit')]

      dummyBtn = CheckButton(self, childName, childSizes, text, None, self.isEnabled\
        , None, self.disabledBgColour, self.inkColour, self.disabledInkColour\
        , startState)
      # This is all that is needed, because the parent _Widget class appends the new CheckButton to self.childList and also adds it to self.rootWidget._widgetDict[child.name]. We can throw the reference in dummyBtn away since we store it thus elsewhere.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      noChildWasClicked = True # default

      if not self.children is None:
        (x, y) = lastClickEvent.getCursorXY()

        for i in range(len(self.children.childList)):
          child = self.children.childList[i]
          if child.contains(x, y) and i!=self.selectedI:
            self.children.childList[self.selectedI].isSelected = False
            self.children.childList[self.selectedI].draw()
            self.selectedI = i
            child.isSelected = True
            child.draw()
            newClickEvent = self.callbackFunction(self, oldClickEvent)
            noChildWasClicked = False
            break

        else: # no child contained the cursor at the time of mouse click.
          pass

      if noChildWasClicked:
        if self.defaultCallbackFunction is None:
          newClickEvent = None
        else:
          newClickEvent = self.defaultCallbackFunction(self, oldClickEvent)

    else: # RadioButtons is not enabled.
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    if not self.isTransparent:
      self.widgetPlotter.draw(self.isEnabled)

    if self.children is None:
      return

    for child in self.children.childList:
      child.draw()

#.......................................................................
class Canvas(_ClickableWidget):
  """
This is intended to provide a field for the user to display images or drawings on.
  """

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, callbackFunction=None, redrawOnClick=False\
    , bgColour='black', initialDrawFunction=None):

    _ClickableWidget.__init__(self, parent, name, sizeSpecs, callbackFunction\
      , redrawOnClick, True, bgColour, None, None, None)

    self.initialDrawFunction = initialDrawFunction
    self.alreadyDrawnOnce = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def changeEnableState(self, isEnabled):
    pass

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.rootWidget.plotter.getCanvasPlotter(self.sizes[0].range.lo\
      , self.sizes[0].range.hi, self.sizes[1].range.lo, self.sizes[1].range.hi\
      , self.bgColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    if not self.alreadyDrawnOnce:
      self.widgetPlotter.draw()
      if not self.initialDrawFunction is None:
        self.initialDrawFunction(self)
      self.alreadyDrawnOnce = True

###### other canvas methods to make drawing stuff on it easier???

#.......................................................................
class Slider(_ClickableWidget):
  """
A widget with a slider which may be moved with the mouse.
  """
  _defaultStartValue = 0.0

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizeSpecs, callbackFunction, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , isVertical=True, transformObject=None, startValue=None):

   # The purpose of transformObject is to convert the cursor position to the slider value, and vice versa.

    _ClickableWidget.__init__(self, parent, name, sizeSpecs, callbackFunction, True\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour)

    self.transformObject = transformObject
    self.isVertical = isVertical

    if startValue is None:
      self.value = self._defaultStartValue
    else:
      self.value = startValue

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.rootWidget.plotter.getSliderPlotter(self\
      , self.sizes[0].range.lo, self.sizes[0].range.hi\
      , self.sizes[1].range.lo, self.sizes[1].range.hi, self.transformObject\
      , self.isVertical, self.bgColour, self.disabledBgColour, self.inkColour\
      , self.disabledInkColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      (x, y) = lastClickEvent.getCursorXY()
      self.value = self.widgetPlotter.getValue(x, y)
      self.draw(x, y)
      newClickEvent = self.callbackFunction(self, oldClickEvent)
    else: # Slider is not enabled.
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self, x, y):
    self.widgetPlotter.draw(self.isEnabled, x, y)

#.......................................................................
class GUI(Frame):
  """
This class must be the first widget instantiated.
  """

  _doTest=False
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, name, sizeSpecs, plotter=None, isEnabled=True, bgColour=None\
    , childSequenceDir=VERTICAL, defaultCallbackFunction=None, userInitialFunction=None\
    , debug=False):

    if plotter is None:
      if not importDrawWentOk:
        raise ValueError('Module for default plotter object did not import.')
      else:
        self.plotter = drw.Plotter()
    else:
      self.plotter = plotter

    Frame.__init__(self, None, name, sizeSpecs, True, isEnabled\
      , bgColour, None, childSequenceDir, defaultCallbackFunction)

    self.userInitialFunction = userInitialFunction

    self.geob = wge.Geometry(self, self._numAxes)

    self.isSetUp = False

    self._widgetDict = {}

    self.isFirstDraw = True

    self._debug = debug

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doSetUp(self):
    # Calculate the border widths, size and position of every widget.
    if self._debug: print 'Setup: calculating all widget sizes'
    for xOrY in [0,1]:
      self.geob.calcRanges(xOrY)
    if self._debug: print

    if self._debug: self.geob.printAllRanges()

    self.plotter.initializePlot(self.sizes[0].range.lo, self.sizes[0].range.hi\
      , self.sizes[1].range.lo, self.sizes[1].range.hi, self.bgColour)
    self.checkColoursChildren()
    self.setUpPlotter()

    if self._doTest:
      import ppgplot as pgplot
      print 'xxx pgplot.pgqcr(18)=', pgplot.pgqcr(18)

    self.isSetUp = True

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __call__(self):
    if not self.isSetUp: self.doSetUp()

    if self._doTest:
      import ppgplot as pgplot
      print 'yyy pgplot.pgqcr(18)=', pgplot.pgqcr(18)

    self.draw()
    if self._doTest:
      print 'zzz pgplot.pgqcr(18)=', pgplot.pgqcr(18)
    self.isFirstDraw = False

    if not self.userInitialFunction is None:
      self.userInitialFunction(self) # the user could e.g. use this to do an initial drawing on canvasses before blocking for the first mouse click.

    if self._doTest:
      self.plotter.lowLevelPlotter.setColour('paper')
      myci = pgplot.pgqci()
      print myci, pgplot.pgqcr(myci)
      self.plotter.lowLevelPlotter.setFill(True)
      self.plotter.lowLevelPlotter.drawRectangle(1.0,1.0,1.5,1.7)

    # Now enter main loop:
    #
    self.plotter.cursorHandler.exitWasChosen = False
    lastClickEvent = None # With the default Plotter etc, this will set the initialClickEvent in the cursor handler. A user who writes their own cursorHandler must cater for None as an argument to the call in a similar way.
    while not self.plotter.cursorHandler.exitWasChosen:
      newClickEvent = self.plotter.cursorHandler(lastClickEvent)
      newClickEventCopy = newClickEvent.copy() # just to avoid possible side-effects with the next call.
      modifiedClickEvent = self.doOnMouseClick(newClickEvent) # this is where the user's CBF are called.
      if modifiedClickEvent is None:
        lastClickEvent = newClickEventCopy
      else:
        lastClickEvent = modifiedClickEvent

    self.plotter.terminatePlot()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyClickEvent:
    def getCursorXY(self):
      return (None,None)

    def copy(self):
      return DummyClickEvent()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyCursor:
    def __init__(self, exitWasChosen=False, newCsrXY=(0.0, 0.0)):
      self.exitWasChosen = exitWasChosen
      self.newCsrXY = newCsrXY

    def __call__(self, clickEvent):
      userInput = raw_input('exit?')
      if userInput=='y': self.exitWasChosen = True
      return DummyClickEvent()

    def updateCsr(self):
      pass

    def copy(self):
      return DummyCursor(self.exitWasChosen, self.newCsrXY)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class _WidgetPlotter:
    def __init__(self, xLo, xHi, yLo, yHi):
      self.xLo = xLo
      self.xHi = xHi
      self.yLo = yLo
      self.yHi = yHi

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyFramePlotter(_WidgetPlotter):
    def __init__(self, xLo, xHi, yLo, yHi):
      _WidgetPlotter.__init__(self, xLo, xHi, yLo, yHi)

    def draw(self, enabled):
      print 'Drawing Frame with X range [%e,%e] and Y range [%e,%e]' % (self.xLo, self.xHi, self.yLo, self.yHi)
      print

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyLabelPlotter(_WidgetPlotter):
    def __init__(self, xLo, xHi, yLo, yHi, text):
      _WidgetPlotter.__init__(self, xLo, xHi, yLo, yHi)

      self.text = text

    def draw(self, enabled):
      print 'Drawing Label with X range [%e,%e] and Y range [%e,%e]. Text %s' % (self.xLo, self.xHi, self.yLo, self.yHi, self.text)
      print

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyButtonPlotter(_WidgetPlotter):
    def __init__(self, xLo, xHi, yLo, yHi, text):
      _WidgetPlotter.__init__(self, xLo, xHi, yLo, yHi)

      self.text = text

    def draw(self, enabled, isPressed):
      if isPressed:
        print 'Drawing pressed Button with X range [%e,%e] and Y range [%e,%e]. Text %s' % (self.xLo, self.xHi, self.yLo, self.yHi, self.text)
      else:
        print 'Drawing unpressed Button with X range [%e,%e] and Y range [%e,%e]. Text %s' % (self.xLo, self.xHi, self.yLo, self.yHi, self.text)
      print

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyCanvasPlotter(_WidgetPlotter):
    def __init__(self, xLo, xHi, yLo, yHi):
      _WidgetPlotter.__init__(self, xLo, xHi, yLo, yHi)

    def draw(self):
      print 'Drawing blank canvas with X range [%e,%e] and Y range [%e,%e].' % (self.xLo, self.xHi, self.yLo, self.yHi)
      print

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummySliderPlotter(_WidgetPlotter):
    def __init__(self, xLo, xHi, yLo, yHi):
      _WidgetPlotter.__init__(self, xLo, xHi, yLo, yHi)

    #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    def draw(self, enabled, x, y):
      print 'Drawing slider with X range [%e,%e] and Y range [%e,%e]. Cursor=(%f, %f)' % (self.xLo, self.xHi, self.yLo, self.yHi, x, y)
      print

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  class DummyPlotter:
    def __init__(self):
      self.cursorHandler = DummyCursor()

    def initializePlot(self, xLo, xHi, yLo, yHi, bgColour):
      pass

    def checkColour(self, colour):
      return True

    def terminatePlot(self):
      pass

    def getFramePlotter(self, xLo, xHi, yLo, yHi, bgColour=None\
      , disabledBgColour=None, drawGroove=True):
      return DummyFramePlotter(xLo, xHi, yLo, yHi)

    def getLabelPlotter(self, xLo, xHi, yLo, yHi, text, bgColour=None\
      , disabledBgColour=None, inkColour=None, disabledInkColour=None):
      return DummyLabelPlotter(xLo, xHi, yLo, yHi, text)

    def getButtonPlotter(self, xLo, xHi, yLo, yHi, text, bgColour=None\
      , disabledBgColour=None, inkColour=None, disabledInkColour=None):
      return DummyButtonPlotter(xLo, xHi, yLo, yHi, text)

    def getCanvasPlotter(self, xLo, xHi, yLo, yHi, bgColour=None):
      return DummyCanvasPlotter(xLo, xHi, yLo, yHi)

    def getSliderPlotter(self, xLo, xHi, yLo, yHi, transformObject, isVertical, bgColour=None\
      , disabledBgColour=None, inkColour=None, disabledInkColour=None):
      return DummySliderPlotter(xLo, xHi, yLo, yHi)



  dummyPlotter = DummyPlotter()

  sizeSpecs = [Size('exact', 10.0)\
             , Size('exact', 3.0)]
  gui = GUI('window', sizeSpecs, dummyPlotter, childSequenceDir=HORIZONTAL, debug=True)
  sizeSpecs = [Size('exact', 3.0)\
             , Size('exact', 2.0)]
  b0 = Button(gui, 'b0', sizeSpecs, 'Hi there', None)
  sizeSpecs = [Size('exact', 5.0)\
             , Size('exact', 2.5)]
  f0 = Frame(gui, 'f0', sizeSpecs)
  sizeSpecs = [Size('exact', 3.0)\
             , Size('expandToFit', None)]
  b00 = Button(f0, 'b00', sizeSpecs, 'Flobs', None)
  sizeSpecs = [Size('exact', 3.0)\
             , Size('expandToFit', None)]
  b01 = Button(f0, 'b01', sizeSpecs, 'More flobs', None)
  sizeSpecs = [Size('exact', 3.0)\
             , Size('expandToFit', None)]
  r02 = RadioButtons(f0, 'r02', sizeSpecs, ['R0','R1','R2'], None)

  gui()






