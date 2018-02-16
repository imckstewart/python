#!/usr/bin/env python

# Name:                         misc_utils
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

_module_name = 'misc_utils'

#.......................................................................
def fracVal(lowerLimit, upperLimit, fracBetween0and1):
  # The double subtraction from 1 is to ensure that the multipliers
  # of lowerLimit and upperLimit add exactly to 1. If this were not done, numerical
  # rounding effects can cause the result to be, for example, less than
  # lowerLimit for small positive values of fracBetween0and1.
  value = (1.0 - fracBetween0and1) * lowerLimit + (1.0 - (1.0 - fracBetween0and1)) * upperLimit
  return value

