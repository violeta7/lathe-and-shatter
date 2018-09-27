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

from __future__ import print_function,division,absolute_import
import sys
import numpy as np

from simple_svg import normalize_svg

def parse_svg_path(svg, auto_align=False, rand_perturbation=False, rand_seed = 0):


    svg = normalize_svg(svg) # convert to normalized SVG


    class ParseState:
        def __init__(self):
            self.delta = False
            self.keepNext = False
            self.need = 0
            self.value = ''
            self.half = False

    state = ParseState()

    points = []
    values = []
    startValues = [0, 0]
    lastValues = [0, 0]
    nextLastValues = [0, 0]


    def addValue():
        if len(state.value) > 0:
            values.append(float(state.value))
            
            if len(values) == 1:
                if state.half == 'h':
                    values.append(0)
                elif state.half == 'H':
                    values.append(lastValues[1])
                elif state.half == 'v':
                    values.append(values[0])
                    values[0] = 0
                elif state.half == 'V':
                    values.append(values[0])
                    values[0] = lastValues[0]
                #print(values)
            if len(values) == 2:
                if state.delta:
                    values[0] += lastValues[0]
                    values[1] += lastValues[1]
                # points.append(tuple(values))
                points.append(values[:])
                if state.keepNext:
                    nextLastValues[:] = values[:]
                state.need -= 1
                if state.need == 0:
                    lastValues[:] = nextLastValues[:]
                del values[:]
            state.value = ''

    # svg commands ref: https://github.com/hughsk/svg-path-parser
    for i,c in enumerate(svg):
        if c >= '0' and c <= '9' or c == '.':
            state.value += c
        elif c == '-':
            addValue()
            state.value = '-'
        elif c == 'm':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = True
            state.half = False
        elif c == 'c':
            addValue()
            state.keepNext = True
            state.need = 3
            state.delta = True
            state.half = False
        elif c == 'M':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = False
            state.half = False            
        elif c == 'C':
            addValue()
            state.keepNext = True
            state.need = 3
            state.delta = False
            state.half = False            
        elif c == 'H':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = False
            state.half = 'H'
        elif c == 'V':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = False
            state.half = 'V'
        elif c == 'h':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = True
            state.half = 'h'
        elif c == 'v':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = True
            state.half = 'v'
        elif c == 'l':
            addValue()
            startValues[:] = lastValues
            state.keepNext = True
            state.need = 1
            state.delta = True
            state.half = False            
        elif c == ',':
            addValue()
        elif c.isspace(): # c == ' ':
            addValue()
        else:
            print('SVG parsing error:', svg[:i], '^', svg[i:],file=sys.stderr)
            assert False, ('unknown/unsupported code',c,'at',i)

    addValue()

    # adding random perturbations on each nodes in svg profile curve.
    if rand_perturbation:
        _min = np.amin(np.array(points,dtype=float)[:,1])
        _max = np.amax(np.array(points,dtype=float)[:,1])
        
        _range = _max - _min
        pertub_max = _range * rand_perturbation
        
        np.random.seed(rand_seed)
        rand_array = (np.random.rand(len(points), 2) - 0.499999999) * 1.999999999 * pertub_max
        
        print(np.amin(rand_array), np.amax(rand_array))
        
        for i, p in enumerate(points):
            #p[0] = p[0] + rand_array[i,0]
            p[1] = p[1] + rand_array[i,1]
        
    if auto_align:
        _min = np.array(points[0],dtype=float)
        _max = np.array(points[0],dtype=float)

        # get bounding box
        for p in points:
            _min = np.minimum(_min,p)
            _max = np.maximum(_max,p)

        _range = _max - _min
        halfRange = _range * .5

        for p in points:
            p[0] = p[0] - _min[0]
            p[1] = (p[1] - _min[1]) - halfRange[1]

    return points




if __name__ == '__main__':
    example_svg = "m385,854c31,-1 67,-16 95,4c17,11 44,19 58,4c7,-26 -5,-49 -8,-75c-9,-30 -15,-62 -12,-94c-8,-29 -1,-61 2,-91c4,-28 21,-53 31,-80c5,-23 18,-43 33,-61c12,-24 23,-49 27,-76c3,-20 9,-44 1,-64c-13,-22 -39,-33 -54,-53c-16,-13 -38,-24 -30,-50c-15,-8 -42,-2 -25,17c3,33 39,43 58,65c23,20 27,53 26,82c-9,28 -21,56 -30,86c-17,30 -30,63 -48,94c-10,25 -18,52 -25,80c-5,28 3,56 8,84c7,29 9,60 17,89c4,17 0,46 -21,23c-16,-16 -45,-9 -65,-5c-12,12 -52,-4 -39,23"
    print(parse_svg_path(example_svg))

