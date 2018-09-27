# coding: utf-8
# Copyright 2018 Artificial Intelligence Research Institute(AIRI), Korea
#
# This file is part of lathe-and-shatter.
# lathe-and-shatter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lathe-and-shatter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lathe-and-shatter.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import print_function, division, absolute_import
import sys

def liang_barsky_clipper(xmin, ymin, xmax, ymax, x1, y1, x2, y2):
    # defining variables
    p1 = -(x2 - x1)
    p2 = -p1
    p3 = -(y2 - y1)
    p4 = -p3

    q1 = x1 - xmin
    q2 = xmax - x1
    q3 = y1 - ymin
    q4 = ymax - y1

    posarr = [1]
    negarr = [0]

    if p1 == 0 and q1 < 0 or p3 == 0 and q3 < 0:
        print('liang_barsky_clipper: ine is parallel to clipping window',x1,y1,x2,y2,file=sys.stderr)
        return 0, 0, 0, 0, False

    if p1 != 0:
        r1 = q1 / p1
        r2 = q2 / p2
        if p1 < 0:
            negarr.append(r1) # for negative p1, add it to negative array
            posarr.append(r2) # and add p2 to positive array
        else:
            negarr.append(r2)
            posarr.append(r1)

    if p3 != 0:
        r3 = q3 / p3
        r4 = q4 / p4
        if p3 < 0:
            negarr.append(r3)
            posarr.append(r4)
        else:
            negarr.append(r4)
            posarr.append(r3)

    rn1 = max(*negarr) # maximum of negative array
    rn2 = min(*posarr) # minimum of positive array

    if rn1 > rn2:
        # print('liang_barsky_clipper: line is outside the clipping window',x1,y1,x2,y2,file=sys.stderr)
        return 0, 0, 0, 0, False

    xn1 = x1 + p2 * rn1
    yn1 = y1 + p4 * rn1 # computing new points

    xn2 = x1 + p2 * rn2
    yn2 = y1 + p4 * rn2

    if xn1 == yn1 and xn2 == yn2:
        print('liang_barsky_clipper: empty segment',x1,y1,x2,y2,file=sys.stderr)
        return 0, 0, 0, 0, False

    return xn1, yn1, xn2, yn2, True
