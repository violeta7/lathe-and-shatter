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


DEFAULT_TOLERANCE = 0.15
DEFAULT_SIMPLIFY_DISTANCE = 0.001   # range 0.001 ~ 5.0



def flatness(points, offset):
    p1, p2, p3, p4 = np.array(points[offset:offset+4])
    u = np.square(3 * p2 - 2 * p1 - p4)
    v = np.square(3 * p3 - 2 * p4 - p1)
    _max = np.maximum(u,v)
    return _max[0] + _max[1]


def getPointsOnBezierCurveWithSplitting(points, offset, tolerance, newPoints=None):
    outPoints = [] if newPoints is None else newPoints
    if flatness(points, offset) < tolerance:
        # just add the end points of this curve
        outPoints.append(list(points[offset+0]))
        outPoints.append(list(points[offset+3]))
    else:
        # subdivide
        t = 0.5
        p1, p2, p3, p4 = np.array(points[offset:offset+4])

        q1 = lerp(p1, p2, t)
        q2 = lerp(p2, p3, t)
        q3 = lerp(p3, p4, t)

        r1 = lerp(q1, q2, t)
        r2 = lerp(q2, q3, t)

        red = lerp(r1, r2, t)

        # do 1st half
        getPointsOnBezierCurveWithSplitting([p1, q1, r1, red], 0, tolerance, outPoints)
        # do 2nd half
        getPointsOnBezierCurveWithSplitting([red, r2, q3, p4], 0, tolerance, outPoints)
    return outPoints


# gets points across all segments
def getPointsOnBezierCurves(points, tolerance):
    newPoints = []
    numSegments = (len(points) - 1) // 3
    for i in range(numSegments):
        offset = i * 3
        getPointsOnBezierCurveWithSplitting(points, offset, tolerance, newPoints)
    return newPoints


def lerp(a, b, t, to_list=None):
    to_list = isinstance(a, list) if to_list is None else to_list
    result = np.add(a, np.subtract(b, a) * t)
    if to_list:
        result = result.tolist()
    return result


# get distance from two point p1, p2
def distanceSq(p1, p2):
    return np.sum(np.square(np.subtract(p1,p2)),axis=0)


# compute the distance squared from p to the line segment
# formed by v and w
def distanceToSegmentSq(p, v, w):
    l2 = distanceSq(v, w)
    if l2 == 0:
        return distanceSq(p, v)
    t = ((p[0] - v[0]) * (w[0] - v[0]) + (p[1] - v[1]) * (w[1] - v[1])) / l2
    t = max(0, min(1, t))
    return distanceSq(p, lerp(v, w, t))


# compute the distance from p to the line segment
# formed by v and w
def distanceToSegment(p, v, w):
    return np.sqrt(distanceToSegmentSq(p, v, w))


# Ramer Douglas Peucker algorithm
def simplifyPoints(points, start, end, epsilon, newPoints=None):
    outPoints = [] if newPoints is None else newPoints

    # find the most distant point from the line formed by the endpoints
    s = points[start]
    e = points[end - 1]
    maxDistSq = 0
    maxNdx = 1
    for i in range(start+1, end-1):
        distSq = distanceToSegmentSq(points[i], s, e)
        if distSq > maxDistSq:
            maxDistSq = distSq
            maxNdx = i

    # if that point is too far
    if np.sqrt(maxDistSq) > epsilon:

        # split
        # simplifyPoints(points, start, maxNdx + 1, epsilon, outPoints)
        simplifyPoints(points, start, maxNdx, epsilon, outPoints)
        simplifyPoints(points, maxNdx, end, epsilon, outPoints)

    else:

        if np.all(s == e):
            outPoints.extend([s])
        else:
            # add the 2 end points
            outPoints.extend([s,e])

    return outPoints


def bezier_to_lineseg(curve_points, tolerance=DEFAULT_TOLERANCE, simplify_eps=DEFAULT_SIMPLIFY_DISTANCE):
    points = getPointsOnBezierCurves(curve_points, tolerance)
    if simplify_eps > 0:
        new_points = simplifyPoints(points, 0, len(points), simplify_eps)
        points = new_points
    return np.array(points)


# # positions: 직선 세그먼트 시작/끝
# # epsilon: options.distance: 0.001 ~ 5.0
# def splitInnerOuterPaths(positions, epsilon):
#     positions = np.array(positions)
#     yvalues = positions[:,1]
#     # get yminIdx, ymaxIdx
#     yminIdx = np.argmin(yvalues)
#     ymaxIdx = np.argmax(yvalues)

#     innerPath = np.concatenate([positions[yminIdx:],positions[:ymaxIdx+1]],axis=0) # inner path: [ymin:] + [:ymax+1]
#     outerPath = np.flip(positions[ymaxIdx:yminIdx+1],axis=0) # outer path: [ymax:ymin+1]

#     simpleInnerPath = np.array(simplifyPoints(innerPath,0,len(innerPath),epsilon)) # simplify inner
#     print('simpleInnerPath.shape',simpleInnerPath.shape)

#     # get matching simplified outer
#     simple_outer_x = np.interp(simpleInnerPath[:,1],outerPath[:,1],outerPath[:,0]).reshape([-1,1])
#     print('simple_outer_x',simple_outer_x[:5])
#     simple_outer_y = np.interp(simpleInnerPath[:,1],outerPath[:,1],outerPath[:,1]).reshape([-1,1])
#     print('simple_outer_y',simple_outer_y[:5])
#     simpleOuterPath = np.concatenate([simple_outer_x,simple_outer_y],axis=1)
#     print('simpleOuterPath.shape',simpleOuterPath.shape)

#     return simpleInnerPath, simpleOuterPath


########################################################################################


if __name__ == '__main__':
    from parse_svg_path import parse_svg_path
    example_svg = "m385,854c31,-1 67,-16 95,4c17,11 44,19 58,4c7,-26 -5,-49 -8,-75c-9,-30 -15,-62 -12,-94c-8,-29 -1,-61 2,-91c4,-28 21,-53 31,-80c5,-23 18,-43 33,-61c12,-24 23,-49 27,-76c3,-20 9,-44 1,-64c-13,-22 -39,-33 -54,-53c-16,-13 -38,-24 -30,-50c-15,-8 -42,-2 -25,17c3,33 39,43 58,65c23,20 27,53 26,82c-9,28 -21,56 -30,86c-17,30 -30,63 -48,94c-10,25 -18,52 -25,80c-5,28 3,56 8,84c7,29 9,60 17,89c4,17 0,46 -21,23c-16,-16 -45,-9 -65,-5c-12,12 -52,-4 -39,23"
    curve_points = parse_svg_path(example_svg)
    print('curve_points',len(curve_points),curve_points)
    line_segments = bezier_to_lineseg(curve_points, simplify_eps=0.0)
    print('line_segments',len(line_segments),line_segments)
    simplified_line_segments = bezier_to_lineseg(curve_points, simplify_eps=0.001)
    print('simplified_line_segments',len(simplified_line_segments),simplified_line_segments)
