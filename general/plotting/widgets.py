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

How to use the API:
===================
The first class to be instantiated must be 'GUI'. After that, other non-abstract classes (i.e. those whose names don't begin with an underscore) may be instantiated. Each of the non-GUI classes requires a parent, which must be either the GUI instance or an instance of class 'Frame'. Many of the widgets can be supplied with a callback function of the user's choice, which is called if the widget is selected. After all the widgets have been instantiated, the final step is to call the 'GUI' instance. A schematic for use of these classes is as follows:

  # Construct plotterObject

  sizes = [Size(<args>),Size(<args>)]
  mygui = GUI('demo gui', sizes, plotterObject)
  sizes = [Size(<args>),Size(<args>)]
  somewidget = <widget class>(gui, <name>, sizes, <etc>)
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

Widget geometry:
================
The size and placement of any widget depends on other widgets, because widget overlap should be avoided, so they kind of jostle one another for space. The basic relationship to keep in mind is between a Frame object and its children. The root-level GUI is a Frame object, so this applies right from the beginning. Since any child can also be a Frame, and thus have children of its own, the whole thing propagates down as far as the levels go.

Children within a frame may only be arranged in a row. This row may be vertical or horizontal; the choice is made at instantiation of the Frame, via the 'childSequenceDir' argument. A value of 0 means horizontal, 1 means vertical.

Sizes:
......
The size of a widget may be expressly given at its instantiation, but if there are many widgets it can be difficult to calculate all the sizes a priori, particularly taking into account the padding (see later this section). For this reason, three possible size descriptions for each axis are possible at instantiation. These are given in the class attribute Size.possibleDemandStates as 'exact', 'shrinkToFit' and 'expandToFit'. The first of these, 'exact', allows the user to provide the size they want. The second says, make the widget as small as possible provided that it still fits the maximum combined size of its children. The third says, make the widget as large as possible consistent with the size of its Frame. There are a few caveats, i.e choices excluded that make no sense: one cannot choose 'shrinkToFit' for either axis of a non-Frame widget (i.e., a widget which cannot have children), and one cannot choose 'expandToFit' if the parent Frame already is 'shrinkToFit' in the same axis. The parent GUI also may not be 'expandToFit' in either axis.

If the Frame is not 'shrinkToFit' and none of the children is 'expandToFit' then there may be space left in the Frame on that axis. The arrangement of the children in this case is specified by the 'alongJustify' and 'crossJustify' arguments at instantiation of a Frame. 'alongJustify' deals with the arrangements in the sequence direction of the children, 'crossJustify' for the arrangement normal to that. Possible values of the first are 'leftOrDown', 'rightOrUp', 'centre' and 'spread'; the crossJustify possibilities omit 'spread', since this makes no sense.

Padding:
........
Each widget occupies a rectangular area, and its 'size' means just the extent of this area. After the locations of the edges of this rectangle are calculated, they are stored in _Widget.ranges, which is a list of 2 ranges.Range objects, for X and Y axes respectively. To avoid widgets rubbing shoulders as it were, some extra (invisible) padding is provided. On each axis, an external pad can be defined for each widget. The space between two adjacent child widgets A and B is not permitted to be less than (A.outerBuffer[n]+B.outerBuffer[n])/2, where 'n' is either 0 or 1 for the axis in question. There is in addition an inner buffer which only has effect for Frame objects. The closest a widget can approach its parent Frame is Frame.innerBuffer[n]/2.

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
import ranges as ra

importDrawWentOk = False # default
try:
  import draw_widgets as drw
  importDrawWentOk = True
except:
  pass

_dirStrs = ['X','Y']

#.......................................................................
class Size:
  possibleDemandStates = ['shrinkToFit','exact','expandToFit']

  def __init__(self, spaceDemand, size=None):
    if not spaceDemand in self.possibleDemandStates:
      raise ValueError('Demand state %s is not recognized.' % (spaceDemand))

    if spaceDemand=='exact' and size is None:
      raise ValueError('You must provide a size if you specify exact.')

    self.spaceDemand = spaceDemand
    self.size = size

#.......................................................................
class _TextWidget:
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, text):
    self.text = text


#.......................................................................
class _Widget:
  _outerBufferFrac = [0.025,0.025]
  _innerBufferFrac = [0.025,0.025]
  isFrame = False # the default
  isGuiFrame = False # the default

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, isTransparent, isEnabled\
    , bgColour, disabledBgColour, inkColour, disabledInkColour\
    , innerBufferFrac, outerBufferFrac):
    # 'parent' must either be an instance of class Frame, or None.
    # 'sizes' must be a list with 2 elements (one for each axis), each being an instance of class Size.

    self.parent = parent # Must be a Frame object or subclass thereof; or None for the outermost GUI window.
    if not parent is None and name in parent.gui._widgetDict.keys():
      raise ValueError('Name %s is already taken by another widget.' % (name))
    self.name = name

    self.spaceDemand = []
    self.size = []
    for i in range(2):
      if not self.isFrame and sizes[i].spaceDemand=='shrinkToFit':
        raise ValueError("You can't choose 'shrinkToFit' for a non-Frame object")
      self.spaceDemand.append(sizes[i].spaceDemand)
      self.size.append(sizes[i].size)

    self.isTransparent = isTransparent

    if not innerBufferFrac is None:
      self._innerBufferFrac = innerBufferFrac[:]#********* should not change class attributes.

    if not outerBufferFrac is None:
      self._outerBufferFrac = outerBufferFrac[:]

    # The following are not set until we know the size of the outermost GUI frame.
    self.innerBuffer = [None,None]
    self.outerBuffer = [None,None]

    if self.parent is None:
      self.gui = self # this actually works as desired, i.e. the 'self' is an instance of Button, Frame or whatever, not of bare _Widget.
      self.isEnabled = isEnabled
    else:
      for xOrY in [0,1]:
        if self.parent.spaceDemand[xOrY]=='shrinkToFit' and self.spaceDemand[xOrY]=='expandToFit':
          raise ValueError("Parent % space demand is 'shrinkToFit', so this widget may not demand 'expandToFit'." % (_dirStrs[xOrY]))

      self.gui = parent.gui

      if not parent.isFrame:
        raise ValueError('Parent object is not a Frame.')

      self.parent._append(self) # this actually works as desired, i.e. the 'self' is an instance of Button, Frame or whatever, not of bare _Widget.

      if self.parent.isEnabled:
        self.isEnabled = isEnabled
      else:
        self.isEnabled = False # we don't allow a child to be enabled if the parent is not.

    # These can be None; the plotting routines should be able to handle this.
    self.bgColour          = bgColour
    self.disabledBgColour  = disabledBgColour
    self.inkColour         = inkColour
    self.disabledInkColour = disabledInkColour

    self._colours = [\
       {'BG':self.bgColour}\
      ,{'Disabled-BG':self.disabledBgColour}\
      ,{'FG':self.inkColour}\
      ,{'Disabled-FG':self.disabledInkColour}]

    # These are set when the gui is finally run, after the dependency tree is constructed.
    self.ranges = [None,None]
    self.childList = []
    self.redraw = True # if False, just draw the things which will change with user action (e.g. mouse clicks)

    self.widgetPlotter = None

    self._debug=False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def contains(self, x, y):
    if self.ranges[0].contains(x) and self.ranges[1].contains(y):
      return True
    else:
      return False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def enable(self):
    # This is needed because some callbacks may want to toggle this state. Also we need a method particularly for Frame objects, so they can also enable all their children.
    self.isEnabled = True
    self.redraw = True
    self.draw()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def disable(self):
    # This is needed because some callbacks may want to toggle this state. Also we need a method particularly for Frame objects, so they can also disable all their children.
    self.isEnabled = False
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
    return lastClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def checkColoursChildren(self):
    for i in range(len(self._colours)):
      clrStr = self._colours[i].keys()[0]
      colour = self._colours[i][clrStr]

      if not colour is None and not self.gui.plotter.checkColour(colour):
        raise ValueError('%s colour %s is not recognized by the plotter.' % (clrStr, colour))

    for child in self.childList:
      child.checkColoursChildren()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __str__(self, spaces=''):
    myStr  = spaces+'< %s object.\n' % (self.__class__.__name__)
    myStr += spaces+'  name = %s\n' % (self.name)
    if self.ranges[0] is None:
      myStr += spaces+'  .xLo = None\n'
      myStr += spaces+'  .xHi = None\n'
    else:
      myStr += spaces+'  .xLo = %e\n' % (self.ranges[0].lo)
      myStr += spaces+'  .xHi = %e\n' % (self.ranges[0].hi)

    if self.ranges[1] is None:
      myStr += spaces+'  .yLo = None\n'
      myStr += spaces+'  .yHi = None\n'
    else:
      myStr += spaces+'  .yLo = %e\n' % (self.ranges[1].lo)
      myStr += spaces+'  .yHi = %e\n' % (self.ranges[1].hi)

#### more work on this

    for child in self.childList:
      myStr += child.__str__(spaces+'  ')+'\n'

    return myStr + spaces+'>'

#.......................................................................
class _PassiveWidget(_Widget):
  """
A _PassiveWidget object has no callback function.
  """
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, isTransparent, isEnabled\
    , bgColour, disabledBgColour, inkColour, disabledInkColour\
    , innerBufferFrac, outerBufferFrac):

    _Widget.__init__(self, parent, name, sizes, isTransparent, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour\
      , innerBufferFrac, outerBufferFrac)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    return None

#.......................................................................
class _ClickableWidget(_Widget):
  """
An _ClickableWidget object has a callback function (although this can be None, in which case the default is used). I'm also assuming that such objects are non-transparent.
  """
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, callbackFunction, redrawOnClick\
    , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
    , innerBufferFrac, outerBufferFrac):

    # The 'callbackFunction' is expected to take 2 arguments, the first being the widget 'self' object, the second being a ClickEvent object (see module header for a description of this). The callbackFunction is expected to return another object of type ClickEvent, although None is also acceptable. A return of None will cause the parent object of the present widget (which at time of writing must be a Frame) to call its default callback.

    _Widget.__init__(self, parent, name, sizes, False, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour\
      , innerBufferFrac, outerBufferFrac)

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
        self.drawPress()
      newClickEvent = self.callbackFunction(self, oldClickEvent)
    else:
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPress(self):
    raise ex.EmptyMethod()

#.......................................................................
# Now the actual non-abstract widgets:
#.......................................................................
class Frame(_PassiveWidget):
  """
A Frame object primarily is designed to contain other 'child' objects of type _Widget.
  """

  isFrame = True
  possibleAlongJustifies = ['leftOrDown', 'rightOrUp', 'centre', 'spread']
  possibleCrossJustifies = ['leftOrDown', 'rightOrUp', 'centre']

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, isTransparent=False, isEnabled=True\
    , bgColour=None, disabledBgColour=None, innerBufferFrac=None, outerBufferFrac=None\
    , childSequenceDir=1, alongJustify='spread', crossJustify='centre'\
    , defaultCallbackFunction=None):

    _PassiveWidget.__init__(self, parent, name, sizes, isTransparent\
      , isEnabled, bgColour, disabledBgColour, None, None\
      , innerBufferFrac, outerBufferFrac)

    self.childSequenceDir   = childSequenceDir # either 0 for children arrayed in the X direction (horizontally) or 1 for children arrayed in the Y direction.

    if not alongJustify in self.possibleAlongJustifies:
      raise ValueError('alongJustify %s requested for widget %s is not recognized.' % (alongJustify, self.name))

    if not crossJustify in self.possibleCrossJustifies:
      raise ValueError('crossJustify %s requested for widget %s is not recognized.' % (alongJustify, self.name))

    self.alongJustify = alongJustify # justify children within the frame in the direction of their sequence: leftOrDown, rightOrUp, centre or spread.
    self.crossJustify = crossJustify # justify children within the frame normal to their sequence: leftOrDown, rightOrUp or centre.

    self.defaultCallbackFunction = defaultCallbackFunction

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _append(self, child):
    self.childList.append(child)
    self.gui._widgetDict[child.name] = child

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      (x, y) = lastClickEvent.getCursorXY()

      for child in self.childList:
        if child.contains(x, y):
          newClickEvent = child.doOnMouseClick(oldClickEvent)
          break

      else: # no child contained the cursor at the time of mouse click.
        if self.defaultCallbackFunction is None:
          newClickEvent = None
        else:
          newClickEvent = self.defaultCallbackFunction(self, oldClickEvent)

    else: # Frame is not enabled.
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def enable(self):
    self.isEnabled = True
    for child in self.childList:
      child.enable()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def disable(self):
    self.isEnabled = False
    for child in self.childList:
      child.disable()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.gui.plotter.getFramePlotter(self.ranges[0].lo\
      , self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi, self.bgColour\
      , self.disabledBgColour, drawGroove=True)

    for child in self.childList:
      child.setUpPlotter()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    if not self.isTransparent:
      self.widgetPlotter.draw(self.isEnabled)

    for child in self.childList:
      if self.gui._debug: print 'About to draw child %s of %s' % (child.name, self.name)
      child.draw()

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setBuffersForChildren(self, xOrY, spaces=''):
    if self.gui._debug: print spaces+'Setting %s buffers for children of %s' % (_dirStrs[xOrY], self.name)
    for child in self.childList:
      if self.gui._debug: print spaces+'  Child is', child.name
      child.outerBuffer[xOrY] = child._outerBufferFrac[xOrY]*self.gui.size[xOrY]
      child.innerBuffer[xOrY] = child._innerBufferFrac[xOrY]*self.gui.size[xOrY]
      if self.gui._debug: print spaces+'    Inner buffer = %s' % (child.innerBuffer[xOrY])
      if self.gui._debug: print spaces+'    Outer buffer = %s' % (child.outerBuffer[xOrY])
      if child.isFrame:
        child.setBuffersForChildren(xOrY, spaces+'  ')

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def calcTotalSizeParallelChildren(self, xOrY):
    totalChildrenSize = 0.0
    numChildren = len(self.childList)
    for i in range(numChildren):
      child = self.childList[i]

      totalChildrenSize += child.size[xOrY]

      if i<1 or i>=(numChildren-1):
        totalChildrenSize += child.outerBuffer[xOrY]/2.0
      else:
        totalChildrenSize += child.outerBuffer[xOrY]

    return totalChildrenSize

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def calcTotalSizeChildren(self, xOrY, spaces=''):
    # If self.spaceDemand[xOrY]=='expandToFit', this returns the minimum total size of the children; otherwise it returns the absolute total size.
    #
    # The second thing this method does is fix the size of any children which have child.spaceDemand[xOrY]=='shrinkToFit' and set their child.spaceDemand[xOrY] to 'exact'. If self.spaceDemand[xOrY]=='expandToFit', any children which are also 'expandToFit' are left that way; if not, all children are set to 'exact'.
    #
    # The most dense allowed child packing is diagrammed as follows to explain the role of the various sizes and buffers.
    #	 ______________________________________________________________________________
    #   |                                                                              |
    #	|  /- self.innerBuffer/2                               self.innerBuffer/2 -\   |
    #	|<-->                                                                      <-->|
    #   |                            /- (child1.outerBuffer+child2.outerBuffer)/2      |
    #	|     ___________________ <------> _________________           ___________     |
    #	|    |<-- child1.size -->|        |<- child2.size ->| etc         childN  |    |
    #	|    |___________________|        |_________________|          ___________|    |
    #	|     <------------------------------------------------------------------>     |
    #	|                       Total  size  of  children                              |
    #   |______________________________________________________________________________|
    #
    # Thus: total size of children = child1.size
    #	                           + child1.outerBuffer/2
    #	                           + child2.size
    #	                           + child2.outerBuffer
    #	                           + ...
    #	                           + childN-1.size
    #	                           + childN-1.outerBuffer
    #	                           + childN.size
    #	                           + childN.outerBuffer/2
    #
    # I.e. only half the outer buffer is added to the start and end children.
    #
    # Also, self.size[xOrY] in this case should be == self.innerBuffer[xOrY] + total size of children

    if self.gui._debug:
      print spaces+'Calculating total %s size of children of %s' % (_dirStrs[xOrY], self.name)
#      print '>>', self.spaceDemand[xOrY], '<<'
      if self.spaceDemand[xOrY]=='exact':
        print spaces+'%s size of %s is %f' % (_dirStrs[xOrY], self.name, self.size[xOrY])
#      else:
#        print 'Frame %s %s spaceDemand is %s' % (self.name, _dirStrs[xOrY], self.spaceDemand[xOrY])

    numChildren = len(self.childList) # for convenience.
    if numChildren<=0:
      if self.gui._debug: print spaces+'Frame %s has no children.' % (self.name)
      return 0.0

    # First fix the size of all children which have spaceDemand[xOrY]=='shrinkToFit':
    #
    numChildrenWithExpand = 0
    for child in self.childList:
      if self.gui._debug: print spaces+'Child %s %s spaceDemand is %s' % (child.name, _dirStrs[xOrY], child.spaceDemand[xOrY])
      if child.spaceDemand[xOrY]=='shrinkToFit': # child must be a frame.
        child.size[xOrY] = child.innerBuffer[xOrY] + child.calcTotalSizeChildren(xOrY, spaces+'  ')
        child.spaceDemand[xOrY] = 'exact'
        if self.gui._debug: print spaces+'Child.spaceDemand %s shrinkToFit->exact, of size %f in %s.' % (child.name, child.size[xOrY], _dirStrs[xOrY])

      elif child.spaceDemand[xOrY]=='expandToFit':
        numChildrenWithExpand += 1

        # Store the minimum size in child.size[xOrY]:
        child.size[xOrY] = child.innerBuffer[xOrY]
        if child.isFrame:
          child.size[xOrY] += child.calcTotalSizeChildren(xOrY, spaces+'  ') # method returns the minimum total size for child.spaceDemand[xOrY]=='expandToFit'.

      else: # child.spaceDemand[xOrY]=='exact', and we don't need to calculate the size of the child, since it is specified and fixed.
        if child.isFrame:
          # Call the routine (we don't need its result) to fix the size of all children of child:
          child.calcTotalSizeChildren(xOrY, spaces+'  ')
        if self.gui._debug: print spaces+'Child.spaceDemand %s is exact, of size %f in %s.' % (child.name, child.size[xOrY], _dirStrs[xOrY])

    if self.spaceDemand[xOrY]=='shrinkToFit' and numChildrenWithExpand>0: # This should have been checked at the time of creation of each child.
      raise ValueError('bug00')

    # Calculate the minimum space taken up by the children. If we work normal to the sequence of child widgets, this will be the maximum value of the child minima; if we work parallel to the sequence, we add the child minima.
    #
    if self.childSequenceDir==xOrY: # parallel
      minChildSize = self.calcTotalSizeParallelChildren(xOrY)
      if self.gui._debug: print spaces+'Frame %s: min total child size along (%s) = %f' % (self.name, _dirStrs[xOrY], minChildSize)

    else: # we're working normal to the child sequence.
      minChildSize = 0.0
      for child in self.childList:
        if minChildSize < child.size[xOrY]:
          minChildSize = child.size[xOrY]
      if self.gui._debug: print spaces+'Frame %s: min child size across (%s) = %f' % (self.name, _dirStrs[xOrY], minChildSize)

    if self.spaceDemand[xOrY]=='expandToFit' or self.spaceDemand[xOrY]=='shrinkToFit':
      return minChildSize

    # A second purpose of the present method is to set the sizes for all children if we know, or can calculate, the parent size. The possible remaining cases are listed as follows:
    #
    #	self.spaceDemand[xOrY]:   numChildrenWithExpand>0?	What to do:
    #
    #	   'exact'			no			Check there is space. No child action, return minChildSize
    #
    #	   'exact'			yes			Check there is space, dole out space to children, make them all exact; return new size
    #
    # Remember that at this point, self.spaceDemand[xOrY] can only be 'exact'. The children are either 'exact' or 'expandToFit'.

    spareSpace = self.size[xOrY] - self.innerBuffer[xOrY] - minChildSize
    if spareSpace<0:
      raise ValueError('Direction %s: minimum space %e needed by children of %s is larger than its size %e.' % (_dirStrs[xOrY], minChildSize, self.name, self.size[xOrY] - self.innerBuffer[xOrY]))

    if numChildrenWithExpand<=0:
      return minChildSize

    if self.childSequenceDir==xOrY: # parallel
      spareSpacePerChild = spareSpace/float(numChildrenWithExpand)
      for child in self.childList:
        if child.spaceDemand[xOrY]=='expandToFit':
          child.size[xOrY] += spareSpacePerChild
          child.spaceDemand[xOrY] = 'exact'
          if self.gui._debug: print spaces+'Child.spaceDemand %s expandToFit->exact, of size %f in %s.' % (child.name, child.size[xOrY], _dirStrs[xOrY])

          if child.isFrame:
            # Call the routine again (we don't need its result) to fix the size of all children of child:
            child.calcTotalSizeChildren(xOrY, spaces+'  ')

    else: # we're working normal to the child sequence.
      for child in self.childList:
        if child.spaceDemand[xOrY]=='expandToFit':
          child.size[xOrY] = self.size[xOrY] - self.innerBuffer[xOrY]
          child.spaceDemand[xOrY] = 'exact'
          if self.gui._debug: print spaces+'Child.spaceDemand %s expandToFit->exact, of size %f in %s.' % (child.name, child.size[xOrY], _dirStrs[xOrY])

          if child.isFrame:
            # Call the routine again (we don't need its result) to fix the size of all children of child:
            child.calcTotalSizeChildren(xOrY, spaces+'  ')

    return self.size[xOrY] - self.innerBuffer[xOrY]

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def positionChildren(self, xOrY):
    # This must not be called unless self and its children have spaceDemand[xOrY]=='exact'.

    if self.gui._debug: print 'Calculating %s positions of children of %s' % (_dirStrs[xOrY], self.name)

    numChildren = len(self.childList) # for convenience.
    if numChildren<=0:
      return

    if self.ranges[xOrY] is None:
      raise ValueError('You cannot call %s.positionChildren(%d) unless %s.ranges[%d] has been set.' % (self.name, xOrY, self.name, xOrY))

    if self.spaceDemand[xOrY]!='exact':
      raise ValueError("You cannot call %s.positionChildren(%d) unless %s.spaceDemand[%d]=='exact'" % (self.name, xOrY, self.name, xOrY))

    for child in self.childList:
      if child.spaceDemand[xOrY]!='exact':
        raise ValueError("You cannot call %s.positionChildren(%d) unless spaceDemand[%d]=='exact' for child %s" % (self.name, xOrY, xOrY, child.name))

    if self.childSequenceDir==xOrY: # parallel
      totalChildrenSize = self.calcTotalSizeParallelChildren(xOrY)
      spareSpacePerChild = 0.0 # default

      if   self.alongJustify=='leftOrDown':
        startPoint = self.ranges[xOrY].lo + self.innerBuffer[xOrY]/2.0
      elif self.alongJustify=='rightOrUp':
        startPoint = self.ranges[xOrY].hi - self.innerBuffer[xOrY]/2.0 - totalChildrenSize
      elif self.alongJustify=='centre':
        startPoint = (self.ranges[xOrY].lo + self.ranges[xOrY].hi)/2.0 - totalChildrenSize/2.0
      elif self.alongJustify=='spread':
        startPoint = self.ranges[xOrY].lo + self.innerBuffer[xOrY]/2.0

        spareSpace = self.size[xOrY] - self.innerBuffer[xOrY] - totalChildrenSize
        if spareSpace<0:
          spareSpace = 0.0

        spareSpacePerChild = spareSpace/float(numChildren)
      # No 'else' because we tested this at the time of construction.

      if self.gui._debug: print 'Parallel: justify=%s, start point %f, spareSpacePerChild=%f' % (self.alongJustify, startPoint, spareSpacePerChild)

      for i in range(numChildren):
        child = self.childList[i]

        if i<1:
          loBuffer = 0.0
        else:
          loBuffer = child.outerBuffer[xOrY]/2.0

        if i>=(numChildren-1):
          hiBuffer = 0.0 # this does not really get used but I'll include it here just to tie up a possible loose end for diagnostics.
        else:
          hiBuffer = child.outerBuffer[xOrY]/2.0

        xyLo = startPoint + loBuffer + spareSpacePerChild/2.0
        xyHi = xyLo + child.size[xOrY]
        child.ranges[xOrY] = ra.SimpleRange(xyLo, xyHi)
        startPoint += loBuffer + child.size[xOrY] + hiBuffer + spareSpacePerChild # The last one does not get used.

    else: # we're working normal to the child sequence.
      if   self.crossJustify=='leftOrDown':
        startPoint = self.ranges[xOrY].lo + self.innerBuffer[xOrY]/2.0
        for child in self.childList:
          xyLo = startPoint
          xyHi = xyLo + child.size[xOrY]
          child.ranges[xOrY] = ra.SimpleRange(xyLo, xyHi)

      elif self.crossJustify=='rightOrUp':
        startPoint = self.ranges[xOrY].hi - self.innerBuffer[xOrY]/2.0
        for child in self.childList:
          xyHi = startPoint
          xyLo = xyHi - child.size[xOrY]
          child.ranges[xOrY] = ra.SimpleRange(xyLo, xyHi)

      elif self.crossJustify=='centre':
        startPoint = (self.ranges[xOrY].lo + self.ranges[xOrY].hi)/2.0
        for child in self.childList:
          xyLo = startPoint - child.size[xOrY]/2.0
          xyHi = xyLo + child.size[xOrY]
          child.ranges[xOrY] = ra.SimpleRange(xyLo, xyHi)

      # No 'else' because we tested this at the time of construction.

    for child in self.childList:
      if child.isFrame:
        child.positionChildren(xOrY)


#.......................................................................
class Label(_PassiveWidget,_TextWidget):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, text, isEnabled=True, bgColour=None\
    , disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None):

    _PassiveWidget.__init__(self, parent, name, sizes, False\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
      , [0,0], outerBufferFrac)

    _TextWidget.__init__(self, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.gui.plotter.getLabelPlotter(self.ranges[0].lo\
      , self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi\
      , self.text, self.bgColour, self.disabledBgColour, self.inkColour\
      , self.disabledInkColour)



#.......................................................................
class Button(_ClickableWidget,_TextWidget):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, text, callbackFunction, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None):

    _ClickableWidget.__init__(self, parent, name, sizes, callbackFunction, True\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
      , [0,0], outerBufferFrac)

    _TextWidget.__init__(self, text)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.gui.plotter.getButtonPlotter(self.ranges[0].lo\
      , self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi\
      , self.text, self.bgColour, self.disabledBgColour, self.inkColour\
      , self.disabledInkColour)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def drawPress(self):
    self.widgetPlotter.draw(self.isEnabled, isPressed=True)
    time.sleep(0.1)
    self.widgetPlotter.draw(self.isEnabled, isPressed=False)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    self.widgetPlotter.draw(self.isEnabled, isPressed=False)

#.......................................................................
class CheckButton(Button):
  defaultCheckState = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, text, callbackFunction, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None, startState=None):

    Button.__init__(self, parent, name, sizes, text, callbackFunction, isEnabled\
      , bgColour, disabledBgColour, inkColour, disabledInkColour, outerBufferFrac)

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
  def drawPress(self): # inherited from Button, but we don't need it.
    raise ex.EmptyMethod()

#.......................................................................
class RadioButtons(Frame):###, _ClickableWidget):
  defaultRadioI = 0

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, buttonTexts, callbackFunction, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , innerBufferFrac=None, outerBufferFrac=None, childSequenceDir=1, alongJustify='spread'\
    , crossJustify='centre', defaultCallbackFunction=None, startI=None):

    Frame.__init__(self, parent, name, sizes, True, isEnabled\
      , bgColour, disabledBgColour, innerBufferFrac, outerBufferFrac\
      , childSequenceDir, alongJustify, crossJustify\
      , defaultCallbackFunction)

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

      childSizes = [Size('expandToFit'),Size('expandToFit')]

      self._append(CheckButton(self, childName, childSizes, text, None, self.isEnabled\
        , self.bgColour, self.disabledBgColour, self.inkColour, self.disabledInkColour\
        , self._outerBufferFrac, startState))


###    _ClickableWidget.__init__(self, plotter, xLo, xHi, yLo, yHi, callbackFunction, state, enabled, bgColour, inkColour, disabledInkColour)
####### This if there is no problems due to diamond inheritance. Then would not need to set self.callbackFunction above.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doOnMouseClick(self, lastClickEvent):
    oldClickEvent = lastClickEvent.copy() # just to avoid possible side-effects.
    if self.isEnabled:
      (x, y) = lastClickEvent.getCursorXY()
      for i in range(len(self.childList)):
        child = self.childList[i]
        if child.contains(x, y) and i!=self.selectedI:
          self.childList[self.selectedI].isSelected = False
          self.childList[self.selectedI].draw()
          self.selectedI = i
          child.isSelected = True
          child.draw()
          newClickEvent = self.callbackFunction(self, oldClickEvent)
          break

      else: # no child contained the cursor at the time of mouse click.
        if self.defaultCallbackFunction is None:
          newClickEvent = None
        else:
          newClickEvent = self.defaultCallbackFunction(self, oldClickEvent)

    else: # RadioButtons is not enabled.
      newClickEvent = self._doNothingCallback(self, oldClickEvent)

    return newClickEvent

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def draw(self):
    for child in self.childList:
      child.draw()

#.......................................................................
class Canvas(_ClickableWidget):
  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, callbackFunction, redrawOnClick=False\
    , bgColour=None, outerBufferFrac=None, initialDrawFunction=None):

    _ClickableWidget.__init__(self, parent, name, sizes, callbackFunction\
      , redrawOnClick, True, bgColour, None, None, None\
      , [0,0], outerBufferFrac)

    self.initialDrawFunction = initialDrawFunction
    self.alreadyDrawnOnce = False

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def enable(self):
    pass

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def disable(self):
    pass

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.gui.plotter.getCanvasPlotter(self.ranges[0].lo\
      , self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi, self.bgColour)

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
  _defaultStartValue = 0.0

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, parent, name, sizes, callbackFunction, isEnabled=True\
    , bgColour=None, disabledBgColour=None, inkColour=None, disabledInkColour=None\
    , outerBufferFrac=None, isVertical=True, transformObject=None, startValue=None):

   # The purpose of transformObject is to convert the cursor position to the slider value, and vice versa.

    _ClickableWidget.__init__(self, parent, name, sizes, callbackFunction, True\
      , isEnabled, bgColour, disabledBgColour, inkColour, disabledInkColour\
      , [0,0], outerBufferFrac)

    self.transformObject = transformObject
    self.isVertical = isVertical

    if startValue is None:
      self.value = self._defaultStartValue
    else:
      self.value = startValue

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setUpPlotter(self):
    self.widgetPlotter = self.gui.plotter.getSliderPlotter(self, self.ranges[0].lo\
      , self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi, self.transformObject\
      , self.isVertical, self.bgColour, self.disabledBgColour, self.inkColour, self.disabledInkColour)

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

  isGuiFrame = True

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self, name, sizes, plotter, isEnabled=True, bgColour=None\
    , innerBufferFrac=None, childSequenceDir=1, alongJustify='spread'\
    , crossJustify='centre', defaultCallbackFunction=None, userInitialFunction=None, debug=False):

    if plotter is None:
      if not importDrawWentOk:
        raise ValueError('Module for default plotter object did not import.')
      else:
        self.plotter = drw.Plotter()
    else:
      self.plotter = plotter

    Frame.__init__(self, None, name, sizes, True, isEnabled\
      , bgColour, None, innerBufferFrac, [0,0]\
      , childSequenceDir, alongJustify, crossJustify\
      , defaultCallbackFunction)

    self.userInitialFunction = userInitialFunction

    for xOrY in [0,1]:
      if self.spaceDemand[xOrY]=='expandToFit':
        raise ValueError("Space demand style for the GUI may not be 'expandToFit'.")

      if self.size[xOrY] is None:
        raise ValueError("You must specify sizes for the GUI in order that widget borders can be calculated.")

    self.isSetUp = False

    self._widgetDict = {}

    self.isFirstDraw = True

    self._debug = debug

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def doSetUp(self):
    # First we set the borders for all the widgets.
    if self._debug: print 'Setup: setting borders'
    for xOrY in [0,1]:
      self.setBuffersForChildren(xOrY)
      self.outerBuffer[xOrY] = self._outerBufferFrac[xOrY]*self.size[xOrY]
      self.innerBuffer[xOrY] = self._innerBufferFrac[xOrY]*self.size[xOrY]
    if self._debug: print

    # Now we calculate the sizes of every widget.
    if self._debug: print 'Setup: calculating all widget sizes'
    for xOrY in [0,1]:
      # Since the GUI may not have self.spaceDemand[xOrY]=='expandToFit', the call to calcTotalSizeChildren not only sets the sizes of all children but also returns their true total size, not just the minimum value.
      totalSizeChildren = self.calcTotalSizeChildren(xOrY)
      if self.spaceDemand[xOrY]=='shrinkToFit':
        self.size[xOrY] = self.innerBuffer[xOrY] + totalSizeChildren
        self.spaceDemand[xOrY] = 'exact'

      self.ranges[xOrY] = ra.SimpleRange(0.0, self.size[xOrY])
      if self._debug: print
    if self._debug: print

    # Now we need to position them.
    if self._debug: print 'Setup: positioning widgets'
    for xOrY in [0,1]:
      self.positionChildren(xOrY)
    if self._debug: print

    self.plotter.initializePlot(self.ranges[0].lo, self.ranges[0].hi, self.ranges[1].lo, self.ranges[1].hi, self.bgColour)
    if not self.userInitialFunction is None:
      self.userInitialFunction(self) # the user could e.g. use this to do an initial drawing on canvasses before blocking for the first mouse click.

    self.checkColoursChildren()

    self.isSetUp = True

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __call__(self):
    if not self.isSetUp: self.doSetUp()
    self.setUpPlotter()
    self.draw()
    self.isFirstDraw = False

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

  sizes = [Size('exact', 10.0),Size('exact', 3.0)]
  gui = GUI('window', sizes, dummyPlotter, childSequenceDir=0, debug=True)
  sizes = [Size('exact', 3.0),Size('exact', 2.0)]
  b0 = Button(gui, 'b0', sizes, 'Hi there', None)
  sizes = [Size('exact', 5.0),Size('exact', 2.5)]
  f0 = Frame(gui, 'f0', sizes)
  sizes = [Size('exact', 3.0),Size('expandToFit', None)]
  b00 = Button(f0, 'b00', sizes, 'Flobs', None)
  sizes = [Size('exact', 3.0),Size('expandToFit', None)]
  b01 = Button(f0, 'b01', sizes, 'More flobs', None)
  sizes = [Size('exact', 3.0),Size('expandToFit', None)]
  r02 = RadioButtons(f0, 'r02', sizes, ['R0','R1','R2'], None)

  gui()






