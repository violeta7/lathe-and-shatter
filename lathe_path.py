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

# tetgen error workaround
# make cap shape like cone
DENT_CAP = True # tetgen error workaround


# get distance from two point p1, p2
def distanceSq(p1, p2):
    return np.sum(np.square(np.subtract(p1,p2)),axis=0)


# get distance from two point p1, p2
def distance(p1, p2):
    return np.sqrt(distanceSq(p1, p2))


#
def lerp(a, b, t, to_list=None):
    to_list = isinstance(a, list) if to_list is None else to_list
    result = np.add(a, np.subtract(b, a) * t)
    if to_list:
        result = result.tolist()
    return result


# create y-rotation matrix
def yRotation(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [c, 0,-s, 0],
        [0, 1, 0, 0],
        [s, 0, c, 0],
        [0, 0, 0, 1]
    ])


# apply transform matrix to a point
def transformPoint(mat, p):
    assert mat.shape == (4, 4), ('mat.shape',mat.shape)
    _p = np.ones(4)
    _p[:3] = p[:]
    # dst = np.matmul(mat, _p)
    dst = np.matmul(_p, mat)
    assert dst.shape == (4,), ('dst.shape',dst.shape)
    return dst[:3] / dst[3]


#LATHE_MIN_X = 30.0
LATHE_MIN_X = 20.0

def align_curve_for_lathe(points, outPoints=None):
    assert points.ndim == 2 and points.shape[1] == 2

    if outPoints is None:
        outPoints = np.zeros_like(points)

    # get bounding box
    _min, _max = np.amin(points,axis=0), np.amax(points,axis=0)
    _range = _max - _min
    half_range = _range * .5

    outPoints[:] = points - _min + np.array([LATHE_MIN_X, -half_range[1]])

    return outPoints


# rotate around Y axis
def lathe_path(points_,
                start_angle=0.0, # angle to start at (ie 0)
                end_angle=2*np.pi, # angle to end at (ie PI * 2)
                num_divisions=60, # how many quads to make around
                cap_start=True, # true to cap the top
                cap_end=True, # true to cap the bottom
                use_map_xz=False):
    nodes = []
    texcoords = []
    indices = []

    points = align_curve_for_lathe(points_)

    pointsPerColumn = len(points)

    # generate v coordinates using topPointIndex
    assert len(points[0]) == 2
    topPointIndex = np.argmin(points[:,1])  # y 값이 가장 작은 point 의 index

    vcoords = np.zeros([len(points)],dtype=float)

    # 바깥쪽 v 좌표 계산
    # 0..topPointIndex
    outerLength = 0.0
    for i in range(topPointIndex):
        vcoords[i] = outerLength
        outerLength += distance(points[i],points[i+1])
    vcoords[topPointIndex] = outerLength
    vcoords[:topPointIndex+1] /= outerLength

    # 안쪽 v 좌표 계산
    # (n-1)..(topPointIndex+1)
    innerLength = 0.0
    for i in range(len(points)-1,topPointIndex,-1):
        vcoords[i] = innerLength
        innerLength += distance(points[i],points[i-1])
    vcoords[topPointIndex+1:] /= innerLength

    # tex_eps = 1.0 / num_divisions * 1.0e-2

    # generate points
    for division in range(num_divisions):
        u = division / num_divisions
        angle = lerp(start_angle, end_angle, u)
        mat = yRotation(angle)
        for ndx, p in enumerate(points):
            x,y,z = transformPoint(mat,[p[0],p[1],0.])
            nodes.append([x,y,z])
            v = vcoords[ndx]
            texcoords.append([u,v])

    if cap_start:
        # add point on Y access at start
        y_capstart = points[0][1]
        if DENT_CAP: # tetgen error workaround
            y_capstart -= 1.5
        capStartPnt = [0., y_capstart, 0.]
        capStartUV = [0., vcoords[0]]
        capStartIdx = len(nodes)
        nodes.append(capStartPnt)
        texcoords.append(capStartUV)

    if cap_end:
        # add point on Y access at end
        y_capend = points[len(points)-1][1]
        if DENT_CAP:
            y_capend += 1.5
        capEndPnt = [0., y_capend, 0.]
        capEndUV = [0., vcoords[-1]] # [1., 1.] # [u, 1.]
        capEndIdx = len(nodes)
        nodes.append(capEndPnt)
        texcoords.append(capEndUV)


    def add_triangle(a,b,c):
        assert a >= 0 and a < len(nodes) , ('invalid a',a,len(nodes) )
        assert b >= 0 and b < len(nodes) , ('invalid b',b,len(nodes) )
        assert c >= 0 and c < len(nodes) , ('invalid c',c,len(nodes) )
        indices.append([a,b,c])


    # generate indices
    for division in range(num_divisions):
        column1Offset = division * pointsPerColumn
        column2Offset = ( division + 1 ) % num_divisions * pointsPerColumn
        if cap_start:
            a,b,c = capStartIdx,column1Offset,column2Offset
            add_triangle(a,b,c)

        for quad,_ in enumerate(points[:-1]):
            a,b,c = column1Offset+quad, column1Offset+quad+1, column2Offset+quad
            add_triangle(a,b,c)
            a,b,c = column1Offset+quad+1, column2Offset+quad+1, column2Offset+quad
            add_triangle(a,b,c)

        if not cap_start and not cap_end:
            # self closing
            last_quad = len(points) - 1
            a,b,c = column1Offset, column2Offset, column1Offset + last_quad
            add_triangle(a,b,c)
            a,b,c = column2Offset, column2Offset + last_quad, column1Offset + last_quad
            add_triangle(a,b,c)

        if cap_end:
            a,b,c = column1Offset+len(points)-1,capEndIdx,column2Offset+len(points)-1
            add_triangle(a,b,c)

    nodes, texcoords, indices = np.array(nodes), np.array(texcoords), np.array(indices)

    # apply xz map instead of uv if requested
    if use_map_xz:
        _min = np.amin(nodes,axis=0)
        _max = np.amax(nodes,axis=0)
        _dim = (_max - _min)
        texcoords[:,:] = ((nodes - _min) / _dim)[:,[0,2]]

    return nodes, texcoords, indices


#
def getExtents(nodes):
    _min = np.amin(nodes,axis=0).tolist()
    _max = np.amax(nodes,axis=0).tolist()
    return _min, _max


def save_mesh(f, nodes, faces, dimensions = 3, node_attrs = None, node_boundary_markers = None, face_boundary_markers = None):

    has_node_boundary_markers = 0 if node_boundary_markers is None else 1
    has_face_boundary_markers = 0 if face_boundary_markers is None else 1

    num_attrs = 0
    if node_attrs is not None:
        try:
            num_attrs = node_attrs[0].shape[-1]
        except:
            num_attrs = 1

    f.write('# part 1 - node\n')
    f.write('# first line: #points, dimensions, #attributes, has_boundary_markers\n')
    f.write('{:d} {:d} {:d} {:d}\n'.format(len(nodes),dimensions,num_attrs,has_node_boundary_markers)) # 2-attribs, 1-boundary-marker

    f.write('# rest lines: point#, x, y, z, [attributes], [boundary marker]\n')
    for ii,node in enumerate(nodes):
        line = '{:d}'.format(ii+1)
        for value in node:
            line += ' {:f}'.format(value)
        if num_attrs > 0:
            for value in node_attrs[ii]:
                line += ' {:f}'.format(value)
        if has_node_boundary_markers:
            line += ' {:d}'.format(node_boundary_markers[ii])
        f.write(line + '\n')

    f.write('# part 2 - facets\n')
    f.write('{:d} {:d}\n'.format(len(faces) , has_face_boundary_markers))

    for ii,face in enumerate(faces):
        assert len(face) == 3
        line = '{:d}'.format(3)
        for _,v in enumerate(face):
            line += ' {:d}'.format(v+1)
        if has_face_boundary_markers:
            line += ' {:d}'.format(face_boundary_markers[ii])
        f.write(line + '\n')

    f.write('# part 3 - holes\n')
    num_holes = 0
    f.write('{:d}\n'.format(num_holes))

    f.write('# part 4 - region attr list\n')
    num_regions = 0
    f.write('{:d}\n'.format(num_regions))


########################################################################################


import argparse

def parse_args(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_mode',action='store_true')
    parser.add_argument('--output_type',type=str,default='smesh')
    parser.add_argument('--tolerance',type=float,default=0.15,help="default 0.15") # 0.4?
    parser.add_argument('--distance',type=float,default=0.001,help="default 0.001, range 0.001 ~ 5.0")
    parser.add_argument('--divisions',type=int,default=60,help="default 60, range 1 ~ 60") # 16?
    parser.add_argument('--startAngle',type=float,default=0.0,help="default 0.0, range 0.0 ~ 2 * PI")
    parser.add_argument('--endAngle',type=float,default=2*np.pi,help="default 2 * PI, range 0.0 ~ 2 * PI")
    parser.add_argument('--capStart',type=bool,default=True)
    parser.add_argument('--capEnd',type=bool,default=True)
    parser.add_argument('svg_path',type=str)
    args = parser.parse_args(*args, **kwargs)
    return args


if __name__ == '__main__':
    import sys
    import json
    from parse_svg_path import parse_svg_path
    from bezier_to_lineseg import bezier_to_lineseg

    def main():
        args = parse_args()

        if args.test_mode:
            input_svg = "m385,854c31,-1 67,-16 95,4c17,11 44,19 58,4c7,-26 -5,-49 -8,-75c-9,-30 -15,-62 -12,-94c-8,-29 -1,-61 2,-91c4,-28 21,-53 31,-80c5,-23 18,-43 33,-61c12,-24 23,-49 27,-76c3,-20 9,-44 1,-64c-13,-22 -39,-33 -54,-53c-16,-13 -38,-24 -30,-50c-15,-8 -42,-2 -25,17c3,33 39,43 58,65c23,20 27,53 26,82c-9,28 -21,56 -30,86c-17,30 -30,63 -48,94c-10,25 -18,52 -25,80c-5,28 3,56 8,84c7,29 9,60 17,89c4,17 0,46 -21,23c-16,-16 -45,-9 -65,-5c-12,12 -52,-4 -39,23"
        else:
            input_svg = args.svg_path

        curvePoints = parse_svg_path(input_svg)
        points = bezier_to_lineseg(curvePoints, tolerance=args.tolerance, simplify_eps=args.distance)
        nodes, texcoords, indices = lathe_path(points,
                        start_angle=args.startAngle,
                        end_angle=args.endAngle,
                        num_divisions=args.divisions,
                        cap_start=args.capStart,
                        cap_end=args.capEnd)

        if args.output_type == 'smesh':
            save_mesh(sys.stdout, nodes, indices, node_attrs=texcoords)
        elif args.output_type == 'wgljson':
            _min, _max = getExtents(nodes)
            obj = dict(
                arrays=dict(
                    position=np.reshape(nodes,[-1]).tolist(),
                    texcoord=np.reshape(texcoords,[-1]).tolist(),
                    indices=np.reshape(indices,[-1]).tolist(),
                ),
                extents=dict(
                    min=_min,
                    max=_max,
                ),
            )
            json.dump(obj, sys.stdout, ensure_ascii=False, indent=2, allow_nan=False)
        else:
            print(len(nodes), nodes)
            print(len(texcoords), texcoords)
            print(len(indices), indices)

    main()
