#!/usr/bin/env python

# Name:                         ranges
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

_module_name = 'ranges'

ranges_UNDECIDED     = -1
ranges_BISTOOHIGH    = ranges_A_before_B = 0
ranges_A_overlaps_B  =  1
ranges_BISTOOLOW     = ranges_A_after_B  = 2
ranges_BOVERLAPSA_HI =  3
ranges_BOVERLAPSA_LO =  4
ranges_BCONTAINSA    =  5
ranges_BCONTAINSA_LO =  6
ranges_BCONTAINSA_HI =  7
ranges_BISWITHINA    =  8
ranges_BISWITHINA_LO =  9
ranges_BISWITHINA_HI = 10
ranges_BEQUALSA      = 11

#.......................................................................
class SimpleRange:
  """
The value 'None' means the bound is infinite. Note that a range with the start and end value the same is valid.
  """

  def __init__(self, lowerValue=None, upperValue=None):
    self.lo=lowerValue
    self.hi=upperValue
    self.checkWellFormed()

  def checkWellFormed(self):
    if self.lo==None or self.hi==None:
      return True
    elif self.lo <= self.hi:
      return True
    else:
      return False

  def contains(self, x):
    if ( self.lo==None or (self.lo!=None and x>=self.lo))\
    and (self.hi==None or (self.hi!=None and x<=self.hi)):
      return True
    else:
      return False

  def calcNearestToRange(self, x):
    """If x is not within the range, the method returns that bound which is closest to x, plus an indication of which bound was closest."""

    if self.contains(x):
      nearestX = x
      return (nearestX, None)

    if (self.hi == None): # lower limit must be !=None and > x:
      nearestX = self.lo
      lowerBoundWasClosest = True

    elif (self.lo==None): # upper limit must be !=None and < x:
      nearestX = self.hi
      lowerBoundWasClosest = False

    else: # neither end is undefined.
      if (self.hi < x):
        nearestX = self.hi
        lowerBoundWasClosest = False

      else: # (self.lo > x):
        nearestX = self.lo
        lowerBoundWasClosest = True

    return (nearestX, lowerBoundWasClosest)

  def checkOverlap(self, rangeB):
    """
The status return is one of the following:
	None
	ranges_BISTOOLOW
	ranges_BISTOOHIGH
	ranges_BOVERLAPSA_HI
	ranges_BOVERLAPSA_LO
	ranges_BCONTAINSA
	ranges_BCONTAINSA_LO
	ranges_BCONTAINSA_HI
	ranges_BISWITHINA
	ranges_BISWITHINA_LO
	ranges_BISWITHINA_HI
	ranges_BEQUALSA
    """

    ALO_LT_BLO = 1
    ALO_GT_BLO = 2
    ALO_EQ_BLO = 3
    AHI_LT_BHI = 4
    AHI_GT_BHI = 5
    AHI_EQ_BHI = 6

    if rangeB==None:
      return None

    status = ranges_UNDECIDED

#    ! Dispose first of the cases where at least one of the bounds is None:

    if (self.lo == None):
      if (rangeB.lo == None):
        if (self.hi == None):
          if (rangeB.hi == None):
# A:	<------>
# B:	<------>
            status = ranges_BEQUALSA
          else:
# A:	<------>
# B:	<-----x
            status = ranges_BISWITHINA_HI
          #end if
        else: # self.hi != None
          if (rangeB.hi == None):
# A:	<-----x
# B:	<------>
            status = ranges_BCONTAINSA_HI
          else: # rangeB.hi != None
            if (self.hi < rangeB.hi):
# A:	<-----x
# B:	<------x
              status = ranges_BCONTAINSA_HI
            elif (self.hi == rangeB.hi):
# A:	<-----x
# B:	<-----x
              status = ranges_BEQUALSA
            else: # self.hi > rangeB.hi
# A:	<------x
# B:	<-----x
              status = ranges_BISWITHINA_HI
            #end if
          #end if ! rangeB.hi == None
        #end if ! self.hi == None
      else: # rangeB.lo != None
        if (self.hi == None):
          if (rangeB.hi == None):
# A:	<------>
# B:	 x----->
            status = ranges_BISWITHINA_LO
          else: # rangeB.hi != None
# A:	<------>
# B:	 x----x
            status = ranges_BISWITHINA
          #end if
        else: # self.hi != None
          if (rangeB.hi == None):
# A:	<-----x
# B:	 x----->
            status = ranges_BOVERLAPSA_HI
          else: # rangeB.hi != None
            if (self.hi < rangeB.hi):
# A:	<-----x
# B:	 x-----x
              status = ranges_BOVERLAPSA_HI
            elif (self.hi == rangeB.hi):
# A:	<-----x
# B:	 x----x
              status = ranges_BISWITHINA_LO
            else: # self.hi > rangeB.hi
# A:	<------x
# B:	 x----x
              status = ranges_BISWITHINA
            #end if
          #end if ! rangeB.hi == None
        #end if ! self.hi == None
      #end if ! rangeB.lo == None
    else: # self.lo != None
      if (rangeB.lo == None):
        if (self.hi == None):
          if (rangeB.hi == None):
# A:	 x----->
# B:	<------>
            status = ranges_BCONTAINSA_LO
          else:
# A:	 x----->
# B:	<-----x
            status = ranges_BOVERLAPSA_LO
          #end if
        else: # self.hi != None
          if (rangeB.hi == None):
# A:	 x----x
# B:	<------>
            status = ranges_BCONTAINSA
          else: # rangeB.hi != None
            if (self.hi < rangeB.hi):
# A:	 x----x
# B:	<------x
              status = ranges_BCONTAINSA
            elif (self.hi == rangeB.hi):
# A:	 x----x
# B:	<-----x
              status = ranges_BCONTAINSA_LO
            else: # self.hi > rangeB.hi
# A:	 x-----x
# B:	<-----x
              status = ranges_BOVERLAPSA_LO
            #end if
          #end if ! rangeB.hi == None
        #end if ! self.hi == None
      else: # rangeB.lo != None
        if (self.hi == None):
          if (rangeB.hi == None):
            if (self.lo < rangeB.lo):
# A:	 x----->
# B:	  x---->
              status = ranges_BISWITHINA_LO
            elif (self.lo == rangeB.lo):
# A:	 x----->
# B:	 x----->
              status = ranges_BEQUALSA
            else: # self.lo > rangeB.lo
# A:	  x---->
# B:	 x----->
              status = ranges_BCONTAINSA_LO
            #end if
          else: # rangeB.hi != None
            if (self.lo < rangeB.lo):
# A:	 x----->
# B:	  x---x
              status = ranges_BISWITHINA
            elif (self.lo == rangeB.lo):
# A:	 x----->
# B:	 x----x
              status = ranges_BISWITHINA_HI
            else: # self.lo > rangeB.lo
# A:	  x---->
# B:	 x----x
              status = ranges_BOVERLAPSA_LO
            #end if
          #end if ! rangeB.hi == None
        else: # self.hi != None
          if (rangeB.hi == None):
            if (self.lo < rangeB.lo):
# A:	 x-----x
# B:	  x----->
              status = ranges_BOVERLAPSA_HI
            elif (self.lo == rangeB.lo):
# A:	 x-----x
# B:	 x------>
              status = ranges_BCONTAINSA_HI
            else: # self.lo > rangeB.lo
# A:	  x----x
# B:	 x------>
              status = ranges_BCONTAINSA
            #end if
          else: # rangeB.hi != None
# A:	 ?-----?
# B:	 ?-----?
# Leave UNDECIDED to avoid too deep nested ifs. This will be sorted out by a later, separate block of nested ifs.
            pass
          #end if
        #end if ! self.hi == None
      #end if ! rangeB.lo == None
    #end if ! self.lo == None


    if (status != ranges_UNDECIDED): return status

    if (self.hi < rangeB.lo):
# A:	 x-----x
# B:	         x-----x
      status = ranges_BISTOOHIGH
    elif (self.hi == rangeB.lo):
# A:	 x-----x
# B:	       x-----x
      status = ranges_BOVERLAPSA_HI
    #end if

    if (status != ranges_UNDECIDED): return status

    if (self.lo > rangeB.hi):
# A:	         x-----x
# B:	 x-----x
      status = ranges_BISTOOLOW
    elif (self.lo == rangeB.hi):
# A:	       x-----x
# B:	 x-----x
      status = ranges_BOVERLAPSA_LO
    #end if


    if (status != ranges_UNDECIDED): return status

    # From here, ranges_BISTOOLOW and ranges_BISTOOHIGH are no longer possible.


#*** replace by compareRangeBounds?

    if (self.lo > rangeB.lo):
          loStatus = ALO_GT_BLO
    elif (self.lo < rangeB.lo):
          loStatus = ALO_LT_BLO
    else: # self.lo == rangeB.lo
          loStatus = ALO_EQ_BLO
    #end if

    if (self.hi > rangeB.hi):
          hiStatus = AHI_GT_BHI
    elif (self.hi < rangeB.hi):
          hiStatus = AHI_LT_BHI
    else: # self.hi == rangeB.hi
          hiStatus = AHI_EQ_BHI
    #end if

    if loStatus==ALO_LT_BLO:
      if hiStatus==AHI_LT_BHI:
# A:	 x-----x
# B:	  x-----x
        status = ranges_BOVERLAPSA_HI
      elif hiStatus==AHI_GT_BHI:
# A:	 x-------x
# B:	  x-----x
        status = ranges_BISWITHINA
      else: # AHI_EQ_BHI
# A:	 x------x
# B:	  x-----x
        status = ranges_BISWITHINA_LO
      #end select
    elif loStatus==ALO_GT_BLO:
      if hiStatus==AHI_LT_BHI:
# A:	  x---x
# B:	 x-----x
        status = ranges_BCONTAINSA
      elif hiStatus==AHI_GT_BHI:
# A:	  x-----x
# B:	 x-----x
        status = ranges_BOVERLAPSA_LO
      else: # AHI_EQ_BHI
# A:	  x----x
# B:	 x-----x
        status = ranges_BCONTAINSA_LO
      #end select
    else: # loStatus==ALO_EQ_BLO
      if hiStatus==AHI_LT_BHI:
# A:	 x----x
# B:	 x-----x
        status = ranges_BCONTAINSA_HI
      elif hiStatus==AHI_GT_BHI:
# A:	 x------x
# B:	 x-----x
        status = ranges_BISWITHINA_HI
      else: # AHI_EQ_BHI
# A:	 x-----x
# B:	 x-----x
        status = ranges_BEQUALSA
      #end select
    #end select

    if (status==ranges_UNDECIDED):
      raise ValueError('checkOverlap bug0')

    return status

  def overlapsWith(self, rangeB):
    status = self.checkOverlap(rangeB)
    if status==None or status==ranges_BISTOOLOW or status==ranges_BISTOOHIGH:
      return False
    else:
      return True

  def __and__(self, rangeB):
    """Note that this method overloads the '&' operator. You cannot overload 'and' in python. This is only a minor typographical annoyance though; the functionality of the method is unchanged."""

    status = self.checkOverlap(rangeB)

    if status==None or status==ranges_BISTOOLOW or status==ranges_BISTOOHIGH:
      return None
    else:
      if status==ranges_BOVERLAPSA_LO\
      or status==ranges_BCONTAINSA\
      or status==ranges_BCONTAINSA_LO:
        lo = self.lo
      else:
        lo = rangeB.lo

      if status==ranges_BOVERLAPSA_HI\
      or status==ranges_BCONTAINSA\
      or status==ranges_BCONTAINSA_HI:
        hi = self.hi
      else:
        hi = rangeB.hi

    return SimpleRange(lo, hi)

  def __or__(self, rangeB):
    """Note that this method overloads the '|' operator. You cannot overload 'or' in python. This is only a minor typographical annoyance though; the functionality of the method is unchanged."""

    if rangeB==None:
      return SimpleRange(self.lo, self.hi)

    status = self.checkOverlap(rangeB)
    if status==None or status==ranges_BISTOOLOW or status==ranges_BISTOOHIGH:
      raise ValueError('no overlap')
    else:
      if status==ranges_BOVERLAPSA_LO\
      or status==ranges_BCONTAINSA\
      or status==ranges_BCONTAINSA_LO:
        lo = rangeB.lo
      else:
        lo = self.lo

      if status==ranges_BOVERLAPSA_HI\
      or status==ranges_BCONTAINSA\
      or status==ranges_BCONTAINSA_HI:
        hi = rangeB.hi
      else:
        hi = self.hi

    return SimpleRange(lo, hi)

  def __str__(self, spaces=''):
    myStr  = spaces+'<%s.%s instance.\n' % (_module_name, self.__class__.__name__)
    myStr += spaces+'  lo: %f\n' % (self.lo)
    myStr += spaces+'  hi: %f\n' % (self.hi)
    myStr += spaces+'>\n'
    return myStr

  def __repr__(self):
    myStr = 'SimpleRange(%r, %r)' % (self.lo, self.hi)
    return myStr


