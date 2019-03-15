#!/usr/bin/env python

# Name:                         widgeometry
#
# Author: Ian Stewart
#
#    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#    Copyright (C) 2019  Ian M Stewart
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
This module is meant to be used in conjunction with module widgets.py. Its purpose is to calculate the sizes and positions of nested widgets.

Widgets are conceived to be objects arranged in a tree. Each widget thus has a single parent, except the root widget, which has none. Each widget may have 0 or more children.

Each widget occupies an amount of space in a region shaped like an orthotope (i.e. an N-dimensional rectangular region). The spatial range of a widget along any axis direction may not exceed the bounds in that dimension of the spatial range of its parent - i.e., the widgets are spatially nested. Provision is also made for some buffer distance between the range bounds of the parent and those of the children (innerBuffer) as well as between children (outerBuffer). The buffer values are expected to be >=0 but there is nothing to constrain them to that range, so technically the user could generate non-nested widget ranges.

Where a widget has >1 children, these are arranged parallel to one of the spatial axes. Sibling widgets may not overlap each other (although this is technically possible if the user specifies <0 outerBuffers).

The spatial extent and location of each widget is decided for spatial axis di via the method Geometry.calcRanges(di). The decisions for any axis don't depend on the arrangement on any other axis. The user inputs their wishes by including in each widget a list of N WidgetSize objects, one for each spatial axis. Each WidgetSize object contains a 'space demand', which may be one of 'exact', 'shrinkToFit' or 'expandToFit', as well as the desired size (valid only for spaceDemand=='exact'), buffer dimensions, and the justification along that axis of any children.
"""

_module_name = 'widgeometry'

import ranges as ra

#.......................................................................
class Buffer:
  """
Defines either the inner buffer (minimum space between parent and children) or the outer buffer (minimum space between sibling widgets). A Buffer object for each is expected to be supplied when instantiating WidgetSize.
  """
  _possibleStyles = ['asFrac','world']
  def __init__(self, value, style='asFrac'):
    if not style in self._possibleStyles:
      raise ValueError('Bad Buffer style: %s' % (style))

    self.value = value
    self.style = style

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def setWorld(self, guiMaxExtent):
    if self.style=='world': # ignore
      return

    if self.style=='asFrac':
      self.value *= guiMaxExtent

    self.style='world'

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def copy(self):
    return Buffer(self.value, self.style)

#.......................................................................
class WidgetSize:
  """
This is the primary means by which the user can indicate their position and size preferences for widgets. Each widget is expected to contain a list of WidgetSize objects, one for each spatial dimension.
  """
  _possibleDemandStates = ['shrinkToFit','exact','expandToFit']
  _possibleJustifies = ['toLowest', 'toHighest', 'centre', 'spread']

  def __init__(self, spaceDemand, maxExtent=None, outerBuffer=None, innerBuffer=None\
    , childrenJustify='spread'):

    if not spaceDemand in self._possibleDemandStates:
      raise ValueError('Demand state %s is not recognized.' % (spaceDemand))

    if spaceDemand=='exact' and maxExtent is None:
      raise ValueError('You must provide a maxExtent if you specify exact.')

    self.spaceDemand = spaceDemand

    if maxExtent is None:
      self.range = None
    else:
      self.range = ra.SimpleRange(0.0, maxExtent)

    if innerBuffer is None:
      self.innerBuffer = Buffer(0.0)
    else:
      self.innerBuffer = innerBuffer

    if outerBuffer is None:
      self.outerBuffer = Buffer(0.0)
    else:
      self.outerBuffer = outerBuffer

    if not childrenJustify in self._possibleJustifies:
      raise ValueError('childrenJustify state %s is not recognized.' % (childrenJustify))
    else:
      self.childrenJustify = childrenJustify

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def copy(self):
    if self.range is None:
      newSize = WidgetSize(self.spaceDemand, None, self.outerBuffer.copy()\
        , self.innerBuffer.copy(), self.childrenJustify)
    else:
      newSize = WidgetSize(self.spaceDemand, 1.0, self.outerBuffer.copy()\
        , self.innerBuffer.copy(), self.childrenJustify) # the 1 is just to avoid a None, since that could have knock-on effects.
      newSize.range = self.range.copy()

    return newSize
    
#.......................................................................
class Geometry:
  """
This class does the heavy lifting of calculating size and position (in each spatial dimension) of each widget in the tree.
  """
  def __init__(self, rootWidget, epsilon=1.0e-7):
    """
The input argument 'rootWidget' is a generic widget object is expected to contain the following attributes:
    - sizes: a list of N WidgetSize objects, N being the number of spatial dimensions. Each sizes element contains attributes as in the class definition above. 
    - name: a string
    - children: either of value None, or an object with the following attributes:.
        * childList: a list of widget objects
        * childSequenceDir: an integer, the number of the spatial axis (starting of course at 0) parallel to which the children are arrayed.
    """
    self.rootWidget = rootWidget
    self.epsilon    = epsilon

    self.maxNumDims = len(rootWidget.sizes)

    for di in range(self.maxNumDims):
      self._checkSpaceDemands(self.rootWidget, di)

      if self.rootWidget.sizes[di].range is None:
        raise ValueError("Dimension %d: you must specify maxExtent for the root object in order that widget borders can be calculated." % (di))

    maxRootSize = 0.0
    for di in range(self.maxNumDims):
      rootSize = self.rootWidget.sizes[di].range.hi - self.rootWidget.sizes[di].range.lo
      if rootSize > maxRootSize:
        maxRootSize = rootSize

    self._setBuffersForChildren(self.rootWidget, maxRootSize)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkSpaceDemands(self, widget, di):
    # There are several parent-child combinations of spaceDemand which are impossible. The present method screens these out.
    #
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * spaceDemand: a string
    #     - name: a string
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects

    if widget is self.rootWidget and widget.sizes[di].spaceDemand=='expandToFit':
      raise ValueError("Dimension %d: the root object %s may not have spaceDemand=='expandToFit'." % (di, widget.name))

    if widget.children is None: # widget is not a frame.
      if widget.sizes[di].spaceDemand=='shrinkToFit':
        raise ValueError("Dimension %d: widget %s is not a frame and therefore may not have spaceDemand=='shrinkToFit'." % (di, widget.name))

    else: # check the kids.
      for child in widget.children.childList:
        if widget.sizes[di].spaceDemand=='shrinkToFit'\
        and child.sizes[di].spaceDemand=='expandToFit':
          raise ValueError("Dimension %d: it is not permitted that parent %s has spaceDemand=='shrinkToFit' but child %s has spaceDemand=='expandToFit'" % (di, widget.name, child.name))

        self._checkSpaceDemands(child, di)


  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _setBuffersForChildren(self, widget, maxRootSize):
    # This converts any 'asFrac' style buffers into 'world'.
    # 
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * outerBuffer: a Buffer object
    #         * innerBuffer: a Buffer object
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects

    for di in range(self.maxNumDims):
      widget.sizes[di].outerBuffer.setWorld(maxRootSize)
      widget.sizes[di].innerBuffer.setWorld(maxRootSize)

    if widget.children is None:
      return

    for child in widget.children.childList:
      self._setBuffersForChildren(child, maxRootSize)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _checkSizeChildren(self, widget, di):
    # Check that there is no 'exact' frame for which the sum (parallel) or max (perp) of 'exact' kids > its own size.
    # 
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * spaceDemand: a string
    #         * range: a SimpleRange object
    #         * outerBuffer: a Buffer object
    #         * innerBuffer: a Buffer object
    #     - name: a string
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects
    #         * childSequenceDir: an integer, the number of the spatial axis (starting of course at 0) parallel to which the children are arrayed.

    if widget.children is None or len(widget.children.childList)<=0\
    or widget.sizes[di].spaceDemand!='exact':
      return

    availableSpace = widget.sizes[di].range.hi - widget.sizes[di].range.lo
    availableSpace -= 2.0*widget.sizes[di].innerBuffer.value
    if widget.children.childSequenceDir==di:
      # We want to find out how much space in the frame is taken up by 'exact' children. The discarding of 1st and last outer child buffers makes this a little tricky. The way we'll do it is not discard them but add them to the available space right at the start. Then after we subtract the outer bounds from all children, the sum will come out right.
      #
      availableSpace += widget.children.childList[ 0].sizes[di].outerBuffer.value
      availableSpace += widget.children.childList[-1].sizes[di].outerBuffer.value
      for child in widget.children.childList:
        if child.sizes[di].spaceDemand=='exact':
          childSize = child.sizes[di].range.hi - child.sizes[di].range.lo
          availableSpace -= childSize

        availableSpace -= 2.0*child.sizes[di].outerBuffer.value

      if availableSpace + self.epsilon < 0.0:
        raise ValueError("Dimension %d: no space for children in widget %s" % (di, widget.name))

    else: # widget.children.childSequenceDir!=di
      for child in widget.children.childList:
        if child.sizes[di].spaceDemand=='exact':
          childSize = child.sizes[di].range.hi - child.sizes[di].range.lo
          if childSize - self.epsilon > availableSpace:
            raise ValueError("Dimension %d: no space for child %s in widget %s" % (di, child.name, widget.name))

    for child in widget.children.childList:
      self._checkSizeChildren(child, di) # recursive call

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _shrinkChildren(self, widget, di):
    # This is called recursively to fill in extents (actually stored in the range.hi values, since range.lo will be set to zero) for any widget of spaceDemand=='shrinkToFit'. After the extent values are stored, the spaceDemand value of the widget is changed to 'exact'.
    # 
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * spaceDemand: a string
    #         * range: a SimpleRange object
    #         * outerBuffer: a Buffer object
    #         * innerBuffer: a Buffer object
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects
    #         * childSequenceDir: an integer, the number of the spatial axis (starting of course at 0) parallel to which the children are arrayed.

    if widget.children is None:
      # then it is not allowed to have spaceDemand=='shrinkToFit'. Such should already have been screened out in self._checkSpaceDemands().
      return

    # Only widgets which may have children reach here.
    #
    numExpandChildren = 0
    for child in widget.children.childList:
      self._shrinkChildren(child, di) # recursive call
      if child.sizes[di].spaceDemand=='expandToFit':
        numExpandChildren += 1

    if numExpandChildren>0:
      # In this case, widget.sizes[di].spaceDemand may only be 'exact' or 'expandToFit'. The 'shrinkToFit' possibility should already have been excluded in self._checkSpaceDemands(). In this case, there is nothing more we need to do.
      return

    if widget.sizes[di].spaceDemand!='shrinkToFit':
      return

    # We only get to here if numExpandChildren==0 and widget.sizes[di].spaceDemand=='shrinkToFit'.
    #
    totalChildSize = 0.0
    if widget.children.childSequenceDir==di:
      # Add up all the child sizes and set the widget size to that, modulo buffers.
      #
      for child in widget.children.childList:
        totalChildSize += child.sizes[di].range.hi - child.sizes[di].range.lo
        totalChildSize += 2.0*child.sizes[di].outerBuffer.value # we'll lop off the end ones afterwards.

      if len(widget.children.childList)>0:
        totalChildSize -= widget.children.childList[ 0].sizes[di].outerBuffer.value
        totalChildSize -= widget.children.childList[-1].sizes[di].outerBuffer.value

    elif len(widget.children.childList)>0:
      # widget.children.childSequenceDir!=di, and there are some kids. Find max kid width and set widget size to that.
      #
      child = widget.children.childList[0]
      totalChildSize = child.sizes[di].range.hi - child.sizes[di].range.lo
      for ci in range(1,len(widget.children.childList)):
        child = widget.children.childList[ci]
        childSize = child.sizes[di].range.hi - child.sizes[di].range.lo
        if childSize > totalChildSize:
          totalChildSize = childSize

    if widget.sizes[di].range is None:
      widget.sizes[di].range = ra.SimpleRange(0.0, totalChildSize\
                             + 2.0*widget.sizes[di].innerBuffer.value)
    else:
      widget.sizes[di].range.lo = 0.0
      widget.sizes[di].range.hi = totalChildSize + 2.0*widget.sizes[di].innerBuffer.value

    widget.sizes[di].spaceDemand = 'exact'

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _expandChildren(self, widget, di):
    # This is called recursively to fill in extents (actually stored in the range.hi values, since range.lo will be set to zero) for all widgets of spaceDemand=='expandToFit'. After the extent values are stored, the spaceDemand values of such are changed to 'exact'.
    # 
    # Note that self._shrinkChildren() needs to be called before this, to ensure that all of the spaceDemand values are either 'exact' or 'expandToFit'.
    # 
    # Matters are so arranged that widget.sizes[di].spaceDemand=='exact' at the time of call.
    # 
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * spaceDemand: a string
    #         * range: a SimpleRange object
    #         * outerBuffer: a Buffer object
    #         * innerBuffer: a Buffer object
    #     - name: a string
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects
    #         * childSequenceDir: an integer, the number of the spatial axis (starting of course at 0) parallel to which the children are arrayed.

    if widget.children is None or len(widget.children.childList)<=0:
      return

    numExpandChildren = 0
    for child in widget.children.childList:
      if child.sizes[di].spaceDemand=='expandToFit':
        numExpandChildren += 1

    if numExpandChildren > 0:
      # Only frame widgets with >0 expandable kids reach here.
      #
      widgetSize = widget.sizes[di].range.hi - widget.sizes[di].range.lo
      availableSpace = widgetSize - 2.0*widget.sizes[di].innerBuffer.value
      if widget.children.childSequenceDir==di:
        # We want to find out how much free space there is in the frame, and divide it evenly between those children with spaceDemand=='expandToFit'. The discarding of 1st and last outer child buffers makes this a little tricky. The way we'll do it is not discard them but add them to the available space right at the start. Then after we subtract the outer bounds from all children, the sum will come out right.
        #
        availableSpace += widget.children.childList[ 0].sizes[di].outerBuffer.value
        availableSpace += widget.children.childList[-1].sizes[di].outerBuffer.value
        for child in widget.children.childList:
          if child.sizes[di].spaceDemand!='expandToFit':
          # then it must be 'exact' if self._shrinkChildren() has been called.
            childSize = child.sizes[di].range.hi - child.sizes[di].range.lo
            availableSpace -= childSize

          availableSpace -= 2.0*child.sizes[di].outerBuffer.value

        if availableSpace<=0.0:
          raise ValueError("Dimension %d: no space for expanding children in widget %s" % (di, widget.name))

        spacePerWidget = availableSpace/float(numExpandChildren)
        for child in widget.children.childList:
          if child.sizes[di].spaceDemand=='expandToFit':
            if child.sizes[di].range is None:
              child.sizes[di].range = ra.SimpleRange(0.0, spacePerWidget)
            else:
              child.sizes[di].range.lo = 0.0
              child.sizes[di].range.hi = spacePerWidget

            child.sizes[di].spaceDemand = 'exact'

      else: # widget.children.childSequenceDir!=di:
        for child in widget.children.childList:
          if child.sizes[di].spaceDemand=='expandToFit':
            if child.sizes[di].range is None:
              child.sizes[di].range = ra.SimpleRange(0.0, availableSpace)
            else:
              child.sizes[di].range.lo = 0.0
              child.sizes[di].range.hi = availableSpace

            child.sizes[di].spaceDemand = 'exact'

    for child in widget.children.childList:
      self._expandChildren(child, di) # recursive call

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _calcPositionsofChildren(self, widget, di):
    # This must not be called unless self and its children have spaceDemand[xOrY]=='exact'. Note also that we can no longer assume that widget.sizes[di].range.lo==0.
    # 
    # The input argument 'widget' is expected to contain the following attributes:
    #     - sizes: a list of N WidgetSize objects, each of which contains the attibutes: 
    #         * childrenJustify: a string
    #         * range: a SimpleRange object
    #         * outerBuffer: a Buffer object
    #         * innerBuffer: a Buffer object
    #         * childrenJustify: a string.
    #     - children: either of value None, or an object with the following attributes:.
    #         * childList: a list of widget objects
    #         * childSequenceDir: an integer, the number of the spatial axis (starting of course at 0) parallel to which the children are arrayed.

    if widget.children is None or len(widget.children.childList)<=0:
      return

    numChildren = len(widget.children.childList)

    if widget.children.childSequenceDir==di:
      if widget.sizes[di].childrenJustify=='toLowest':
        x = widget.sizes[di].range.lo + widget.sizes[di].innerBuffer.value\
          - widget.children.childList[0].sizes[di].outerBuffer.value
        for ci in range(numChildren):
          child = widget.children.childList[ci]
          x += child.sizes[di].outerBuffer.value
          delta = child.sizes[di].range.hi - child.sizes[di].range.lo
          child.sizes[di].range.lo = x
          child.sizes[di].range.hi = x + delta
          x += delta
          x += child.sizes[di].outerBuffer.value

      elif widget.sizes[di].childrenJustify=='toHighest':
        x = widget.sizes[di].range.hi - widget.sizes[di].innerBuffer.value\
          + widget.children.childList[-1].sizes[di].outerBuffer.value
        for ci in range(numChildren):
          child = widget.children.childList[numChildren-1-ci]
          x -= child.sizes[di].outerBuffer.value
          delta = child.sizes[di].range.hi - child.sizes[di].range.lo
          child.sizes[di].range.lo = x - delta
          child.sizes[di].range.hi = x
          x -= delta
          x -= child.sizes[di].outerBuffer.value

      elif widget.sizes[di].childrenJustify=='centre'\
      or   widget.sizes[di].childrenJustify=='spread':
        totalWidthChildren = 0.0
        for child in widget.children.childList:
          childSize = child.sizes[di].range.hi - child.sizes[di].range.lo
          totalWidthChildren += childSize
          totalWidthChildren += 2.0*child.sizes[di].outerBuffer.value

        totalWidthChildren -= widget.children.childList[ 0].sizes[di].outerBuffer.value
        totalWidthChildren -= widget.children.childList[-1].sizes[di].outerBuffer.value

        if widget.sizes[di].childrenJustify=='centre' or numChildren==1:
          x = 0.5*(widget.sizes[di].range.hi + widget.sizes[di].range.lo)
          x -= 0.5*totalWidthChildren
          x -= widget.children.childList[ 0].sizes[di].outerBuffer.value
          for child in widget.children.childList:
            x += child.sizes[di].outerBuffer.value
            delta = child.sizes[di].range.hi - child.sizes[di].range.lo
            child.sizes[di].range.lo = x
            child.sizes[di].range.hi = x + delta
            x += delta
            x += child.sizes[di].outerBuffer.value

        else: # widget.sizes[di].childrenJustify=='spread' and numChildren>1:
          availableSpace = widget.sizes[di].range.hi - widget.sizes[di].range.lo
          availableSpace -= 2.0*widget.sizes[di].innerBuffer.value
          addedSpaceBetweenChildren = (availableSpace - totalWidthChildren)\
                                    /float(numChildren - 1)

          x = widget.sizes[di].range.lo + widget.sizes[di].innerBuffer.value\
            - widget.children.childList[0].sizes[di].outerBuffer.value
          for ci in range(numChildren):
            child = widget.children.childList[ci]
            x += child.sizes[di].outerBuffer.value
            delta = child.sizes[di].range.hi - child.sizes[di].range.lo
            child.sizes[di].range.lo = x
            child.sizes[di].range.hi = x + delta
            x += delta
            x += child.sizes[di].outerBuffer.value
            x += addedSpaceBetweenChildren

    else: # widget.children.childSequenceDir!=di:
      if widget.sizes[di].childrenJustify=='toLowest':
        x = widget.sizes[di].range.lo + widget.sizes[di].innerBuffer.value
        for child in widget.children.childList:
          delta = child.sizes[di].range.hi - child.sizes[di].range.lo
          child.sizes[di].range.lo = x
          child.sizes[di].range.hi = x + delta

      elif widget.sizes[di].childrenJustify=='toHighest':
        x = widget.sizes[di].range.hi - widget.sizes[di].innerBuffer.value
        for child in widget.children.childList:
          delta = child.sizes[di].range.hi - child.sizes[di].range.lo
          child.sizes[di].range.lo = x - delta
          child.sizes[di].range.hi = x

      elif widget.sizes[di].childrenJustify=='centre' or widget.sizes[di].childrenJustify=='spread':
        x = 0.5*(widget.sizes[di].range.hi + widget.sizes[di].range.lo)
        for child in widget.children.childList:
          delta = child.sizes[di].range.hi - child.sizes[di].range.lo
          child.sizes[di].range.lo = x - 0.5*delta
          child.sizes[di].range.hi = x + 0.5*delta

    for child in widget.children.childList:
      self._calcPositionsofChildren(child, di) # recursive call.

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def calcRanges(self, di):
    """
The 'self.rootWidget' object is assumed to define a tree of generic widgets, each of which has a range object in each of N dimensions. The range has a lo value and a high value. The purpose of the present method is to calculate the ranges along the dimension 'di'.

The calculation makes use of the following information.

  - For each widget that has children, the children are arranged either parallel to dimension di, or parallel to some other dimension, in which case they are necessarily perpendicular to di.

  - For di-parallel children, the ranges in di of no two children may overlap.

  - No child widget may have a range in any dimension which extends beyond the range of its parent.

  - Each widget has, for each dimension, a WidgetSize object which defines the user preferences for the size and position of the widget (and its children, if any).

  - Each widget except the root widget is expected to have (as part of the WidgetSize object for that dimension) an outer buffer, which defines the minimum space between sibling widgets.

  - Each widget which may have children is expected to have (as part of the WidgetSize object for that dimension) an inner buffer, which defines the minimum space between a parent widget and its children.
    """

    self._checkSizeChildren(self.rootWidget, di)

    self._shrinkChildren(self.rootWidget, di)

    # After this, there should be no widgets anywhere in the tree with spaceDemand=='shrinkToFit'.

    self._expandChildren(self.rootWidget, di)

    # After this, all widgets should have spaceDemand=='exact'.
    #
    # All the sizes were fixed, but we have to use the justify information to position children within their parents:
    #
    self._calcPositionsofChildren(self.rootWidget, di)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def _printChildRanges(self, widget, di, spaces):
    myStr = "%s%s: " % (spaces, widget.name)
    if widget.sizes[di].range is None:
      myStr += "None"
    else:
      myStr += "%5.2f to %5.2f" % (widget.sizes[di].range.lo, widget.sizes[di].range.hi)
    myStr += "  "+widget.sizes[di].spaceDemand
    print myStr

    if widget.children is None:
      return

    for child in widget.children.childList:
      self._printChildRanges(child, di, spaces+'  ')

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def printAllRanges(self):
    for di in range(len(self.rootWidget.sizes)):
      print "Ranges for axis %d" % (di)
      print "================="
      self._printChildRanges(self.rootWidget, di, '')
      print

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':

  import math_utils as ma

  class TestChildren:
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

  class TestWidget:
    def __init__(self, parent, name, sizes, childSequenceDir=None):

      self.parent = parent
      self.name = name
      self.sizes = sizes

      if childSequenceDir is None:
        self.children = None
      else:
        self.children = TestChildren([], childSequenceDir)

      self._numAxes = len(self.sizes)

      if parent is None:
        self.rootWidget = self
      else:
        self.rootWidget = parent.rootWidget
        if parent.children is None: # not ideal - you should set up the parent widget to be a Frame by supplying it with a non-None childSequenceDir when instantiating.
          parent.children = TestChildren([self])
        else:
          parent.children.childList.append(self)

    def _printChildRanges(self, widget, di, spaces):
      myStr = "%s%s: " % (spaces, widget.name)
      if widget.sizes[di].range is None:
        myStr += "None"
      else:
        myStr += "%5.2f to %5.2f" % (widget.sizes[di].range.lo, widget.sizes[di].range.hi)
      myStr += "  "+widget.sizes[di].spaceDemand
      print myStr

      if widget.children is None:
        return

      for child in widget.children.childList:
        self._printChildRanges(child, di, spaces+'  ')

    def printAllRanges(self):
      for di in range(len(self.sizes)):
        print "Ranges for axis %d" % (di)
        print "================="
        self._printChildRanges(self.rootWidget, di, '')
        print

  allTestsPassed = True # default
  if allTestsPassed:
    # Buffer.setWorld(rootExtent)
    #
    bufferVal = 0.02
    rootExtent = 6.5
    buf = Buffer(bufferVal)
    buf.setWorld(rootExtent)
    if not ma.approxEqual(buf.value, 0.13):
      print "buf.value expected to equal %e but instead we have %e" % (0.13, buf.value)
      allTestsPassed = False
    if buf.style!='world':
      print "buf.style should = 'world' but instead we have", buf.style
      allTestsPassed = False

  gui = TestWidget(None, 'gui'\
    , [WidgetSize('exact', 10.0, Buffer(0.0), Buffer(0.01), 'spread')\
    ,  WidgetSize('exact',  6.0, Buffer(0.0), Buffer(0.01), 'toLowest')]\
    , childSequenceDir=0)


  a0 = TestWidget(gui, 'a0'\
    , [WidgetSize('shrinkToFit', None, Buffer(0.01), Buffer(0.01), 'toHighest')\
    ,  WidgetSize('exact',        4.0, Buffer(0.01), Buffer(0.01), 'centre')]\
    , childSequenceDir=1)

  a1 = TestWidget(gui, 'a1'\
    , [WidgetSize('exact',        3.0, Buffer(0.01), Buffer(0.01), 'spread')\
    ,  WidgetSize('expandToFit', None, Buffer(0.01), Buffer(0.01), 'centre')]\
    , childSequenceDir=0)

  a2 = TestWidget(gui, 'a2'\
    , [WidgetSize('shrinkToFit', None, Buffer(0.01), Buffer(0.01), 'centre')\
    ,  WidgetSize('exact',        4.0, Buffer(0.01), Buffer(0.01), 'centre')]\
    , childSequenceDir=1)

  a3 = TestWidget(gui, 'a3'\
    , [WidgetSize('exact',        2.0, Buffer(0.01), Buffer(0.01), 'centre')\
    ,  WidgetSize('shrinkToFit', None, Buffer(0.01), Buffer(0.01), 'toLowest')]\
    , childSequenceDir=1)


  a00 = TestWidget(a0, 'a00'\
    , [WidgetSize('exact', 1.0, Buffer(0.01))\
    ,  WidgetSize('exact', 1.5, Buffer(0.01))])

  a01 = TestWidget(a0, 'a01'\
    , [WidgetSize('exact', 0.5, Buffer(0.01))\
    ,  WidgetSize('exact', 1.0, Buffer(0.01))])


  a10 = TestWidget(a1, 'a10'\
    , [WidgetSize('exact', 1.0, Buffer(0.01))\
    ,  WidgetSize('exact', 1.0, Buffer(0.01))])

  a11 = TestWidget(a1, 'a11'\
    , [WidgetSize('exact',        0.7, Buffer(0.01), Buffer(0.01))\
    ,  WidgetSize('shrinkToFit', None, Buffer(0.01), Buffer(0.02))]\
    , childSequenceDir=1) # means it is flagged as a Frame widget even though we don't plan to give it any children.


  a20 = TestWidget(a2, 'a20'\
    , [WidgetSize('exact',        0.2, Buffer(0.01))\
    ,  WidgetSize('expandToFit', None, Buffer(0.01))])

  a21 = TestWidget(a2, 'a21'\
    , [WidgetSize('exact', 1.0, Buffer(0.01))\
    ,  WidgetSize('exact', 0.2, Buffer(0.01))])

  a22 = TestWidget(a2, 'a22'\
    , [WidgetSize('exact',        0.6, Buffer(0.01), Buffer(0.01))\
    ,  WidgetSize('expandToFit', None, Buffer(0.01), Buffer(0.01), 'toHighest')]\
    , childSequenceDir=1)

  a220 = TestWidget(a22, 'a220'\
    , [WidgetSize('expandToFit', None, Buffer(0.01))\
    ,  WidgetSize('exact',        0.2, Buffer(0.01))])

  a23 = TestWidget(a2, 'a23'\
    , [WidgetSize('exact',        0.4, Buffer(0.01))\
    ,  WidgetSize('expandToFit', None, Buffer(0.01))])


  a30 = TestWidget(a3, 'a30'\
    , [WidgetSize('exact', 1.0, Buffer(0.01))\
    ,  WidgetSize('exact', 1.0, Buffer(0.01))])

  a31 = TestWidget(a3, 'a31'\
    , [WidgetSize('expandToFit', None, Buffer(0.02))\
    ,  WidgetSize('exact',        0.5, Buffer(0.02))])

  a32 = TestWidget(a3, 'a32'\
    , [WidgetSize('exact', 0.4, Buffer(0.01))\
    ,  WidgetSize('exact', 0.8, Buffer(0.01))])


  geob = Geometry(gui, 2)

  geob.calcRanges(0)
  geob.calcRanges(1)
  geob.printAllRanges()

  if allTestsPassed:
    print 'Passed all tests'




