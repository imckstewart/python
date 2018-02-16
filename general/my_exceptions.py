#!/usr/bin/env python

# Name:                         my_exceptions
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

_module_name = 'my_exceptions'

class EmptyMethod(Exception):
  def __str__(self):
    return 'This method should be implemented in a subclass.'

class UnrecognizedChoiceObject(Exception):
  def __init__(self, choiceObject, message=None):
    self.choiceObject = choiceObject
    self.message = message
  def __str__(self):
    if self.message==None:
      return 'Choice %s was not recognized.' % (str(self.choiceObject))
    else:
      return '%s: choice %s was not recognized.' % (self.message, str(self.choiceObject))


