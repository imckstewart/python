#!/usr/bin/env python

# Name:                         colourmap
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
This defines a colourmap object which has methods for reading and writing a colourmap from file.
"""

_module_name = 'colourmap'

#import os
import numpy as nu
#import ppgplot as pgplot

#import pgplot_interface as pgi
#import draw_widgets as drw
#import widgets


#.......................................................................
class _HueGraph:
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
    newHueGraph = _HueGraph(self._firstH, self._lastH)
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
#  _defaultRedFirstHue = 0.0
#  _defaultGrnFirstHue = 0.0
#  _defaultBluFirstHue = 0.0
#  _defaultRedLastHue = 1.0
#  _defaultGrnLastHue = 1.0
#  _defaultBluLastHue = 1.0
#  _numHues = 3


  _defaultFirstHues = [0.0,0.0,0.0]
  _defaultLastHues  = [1.0,1.0,1.0]
  _hueNames = ['red','grn','blu']
  _numHues = len(_hueNames)

  #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  def __init__(self):
    self.hueGraphs = []
    for hueI in range(self._numHues):
      self.hueGraphs.append(_HueGraph(self._defaultFirstHues[hueI], self._defaultLastHues[hueI]))

    self.actionHistory = ActionHistory()

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

      tempHueGraphs.append(_HueGraph(first, last))

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

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':
  pass

