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
from traceback import print_exc
import sys
import re
import matplotlib.path as mpath



# python2-3 workaround
try: from itertools import izip as zip
except: pass # izip = zip

def pairwise(iterable):
    a = iter(iterable)
    return zip(a,a) # izip(a, a)



# STOP MOVETO LINETO CURVE3 CURVE4 CLOSEPOLY
SVG_CODE_MAP = dict(zip('MmLlCcSsQqTtHhVvZzAa', [
    mpath.Path.MOVETO,
    mpath.Path.MOVETO,
    mpath.Path.LINETO,
    mpath.Path.LINETO,
    mpath.Path.CURVE4,
    mpath.Path.CURVE4,
    mpath.Path.CURVE4,
    mpath.Path.CURVE4,
    mpath.Path.CURVE3,
    mpath.Path.CURVE3,
    mpath.Path.CURVE3,
    mpath.Path.CURVE3,
    mpath.Path.LINETO,
    mpath.Path.LINETO,
    mpath.Path.LINETO,
    mpath.Path.LINETO,
    mpath.Path.CLOSEPOLY,
    mpath.Path.CLOSEPOLY,
    mpath.Path.STOP,
    mpath.Path.STOP,
]))

SVG_CODE_NAME_MAP = {
    mpath.Path.MOVETO: 'MOVETO',
    mpath.Path.LINETO: 'LINETO',
    mpath.Path.CURVE4: 'CURVE4',
    mpath.Path.CURVE3: 'CURVE3',
    mpath.Path.LINETO: 'LINETO',
    mpath.Path.CLOSEPOLY: 'CLOSEPOLY',
    mpath.Path.STOP: 'STOP',
}


def to_number(s,to_integer=True):
    try:
        if to_integer:
            return int(float(str(s).strip()))
        else:
            return float(str(s).strip())
    except:
        print(('number parsing error',s),file=sys.stderr)


def parse_number_list(number_list_str):
    res = [to_number(s) for s in re.split(r'[,\s]+',number_list_str.strip())]
    #print(('trace','parse_number_list',res,'number_list_str',number_list_str),file=sys.stderr)
    return res


def parse_coord_list(coord_list_str):
    res = [(to_number(_x),to_number(_y)) for _x, _y in pairwise(re.split(r'[,\s]+',coord_list_str.strip()))]
    #print(('trace','parse_coord_list',res,'coord_list_str',coord_list_str),file=sys.stderr)
    return res


def normalize_svg(svg_str):

    svg_seq = [x for x in re.split(r'([MLCSQTmlcsqtHhVvZzAa])',svg_str) if len(x.strip()) > 0]

    simplified_seq = []

    i = 0
    while i < len(svg_seq):
        code = svg_seq[i]

        if code in 'Cc': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2 ...
            coord_list = parse_coord_list(svg_seq[i+1])
            if 0 != len(coord_list) % 3:
                print(('warning', 'len coord_list % 3'))
            for p in range(0,len(coord_list),3):
                sub_list = coord_list[p:p+3]
                if len(sub_list) == 3:
                    seq = code + ','.join(['{},{}'.format(x,y) for x, y in sub_list])
                    simplified_seq.append(seq)
            i += 2
            continue

        if code in 'SsQq': # <code> x1 y1 x2 y2 ...
            coord_list = parse_coord_list(svg_seq[i+1])
            for p in range(0,len(coord_list),2):
                sub_list = coord_list[p:p+2]
                if len(sub_list) == 2:
                    seq = code + ','.join(['{},{}'.format(x,y) for x, y in sub_list])
                    simplified_seq.append(seq)
            i += 2
            continue

        if code in 'MmLlTt': # <code> x1 y1 x2 y2 ...
            coord_list = parse_coord_list(svg_seq[i+1])
            for x, y in coord_list:
                simplified_seq.append('{}{},{}'.format(code,x,y))
            i += 2
            continue

        if code in 'HhVv': # <code> x1 x2 ...
            number_list = parse_number_list(svg_seq[i+1])
            for x in number_list:
                simplified_seq.append('{}{}'.format(code,x))
            i += 2
            continue

        if code in 'Zz': # Z or z
            simplified_seq.append('{}'.format(code))
            i += 1
            continue

        # if code == 'A': # A rx ry a f1 f2 x y
        #     pass

        # if code == 'a': # a rx ry a f1 f2 dx dy
        #     pass

        # if code == '\n':
        #     i += 1
        #     continue # skip

        raise RuntimeError(('unknown code',code))

    simplified_svg = ''.join(simplified_seq)

    return simplified_svg


def get_abs_coords(code, coord_list, last_coord):
    #print("coord_list:",end='')
    #print(coord_list)
    if code.isupper():
        if code == 'H':
            return [(coord_list[0], last_coord[1])]
        elif code == 'V':
            return [(last_coord[0], coord_list[1])]
        else:
            return coord_list

    # lower case code (relative)
    new_coord_list = []
    if code == 'h':
        for dx in coord_list:
            lx, ly = last_coord[0] + dx, last_coord[1]
            new_coord_list.append((lx, ly))
            last_coord[:] = lx, ly
    elif code == 'v':
        for dy in coord_list:
            lx, ly = last_coord[0], last_coord[1] + dy
            new_coord_list.append((lx, ly))
            last_coord[:] = lx, ly
    else:
        for dx, dy in coord_list:
            lx, ly = last_coord[0] + dx, last_coord[1] + dy
            new_coord_list.append((lx, ly))
            last_coord[:] = lx, ly
    #print("new:",end='')
    #print(new_coord_list)
    return new_coord_list


def svg_to_paths(svg_str,debug_curves=False,trace_codes=False):

    # simplified_svg_str = normalize_svg(svg_str)

    svg_seq = [x for x in re.split(r'([MLCSQTmlcsqtHhVvZzAa])',svg_str) if len(x.strip()) > 0]

    start_coord = [0.0, 0.0]
    last_coord  = [0.0, 0.0]

    path_verts = []
    path_codes = []

    i = 0
    while i < len(svg_seq):
        code = svg_seq[i]

        if code in 'Cc': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2
            prev_last_coord = list(last_coord) # copy last coord
            coord_list = get_abs_coords(code,parse_coord_list(svg_seq[i+1]),last_coord)
            if 0 != len(coord_list) % 3:
                print(('warning', 'len coord_list % 3'))
            for p in range(0,len(coord_list),3):
                sub_list = coord_list[p:p+3]
                # # first coordinate = move to last coordinate
                # x, y = prev_last_coord
                # path_code = mpath.Path.MOVETO
                # path_codes.append(path_code)
                # path_verts.append((x,y))
                # if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
                # rest coordinates = curve4
                for x, y in sub_list:
                    path_code = mpath.Path.LINETO if debug_curves else SVG_CODE_MAP[code]
                    path_codes.append(path_code)
                    path_verts.append((x,y))
                    if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            i += 2
            continue

        if code in 'Ss': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2 ...
            coord_list = get_abs_coords(code,parse_coord_list(svg_seq[i+1]),last_coord)
            for p in range(0,len(coord_list),2):
                sub_list = coord_list[p:p+2]
                for x, y in sub_list:
                    path_code = mpath.Path.LINETO if debug_curves else SVG_CODE_MAP[code]
                    path_codes.append(path_code)
                    path_verts.append((x,y))
                    if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            i += 2
            continue

        if code in 'Qq': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2 ...
            prev_last_coord = list(last_coord)
            coord_list = get_abs_coords(code,parse_coord_list(svg_seq[i+1]),last_coord)
            for p in range(0,len(coord_list),2):
                sub_list = coord_list[p:p+2]
                # # first coordinate = move
                # x, y = prev_last_coord[0]
                # path_code = mpath.Path.MOVETO
                # path_codes.append(path_code)
                # path_verts.append((x,y))
                # if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
                # rest coordinates = curve4
                for x, y in sub_list:
                    path_code = mpath.Path.LINETO if debug_curves else SVG_CODE_MAP[code]
                    path_codes.append(path_code)
                    path_verts.append((x,y))
                    if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            i += 2
            continue

        if code in 'Tt': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2 ...
            coord_list = get_abs_coords(code,parse_coord_list(svg_seq[i+1]),last_coord)
            for x, y in coord_list:
                path_code = SVG_CODE_MAP[code]
                path_codes.append(path_code)
                path_verts.append((x,y))
                if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            if code == 'M' or code == 'm':
                start_coord[:] = last_coord
            i += 2
            continue

        if code in 'MmLl': # <code> x1 y1 x2 y2 ... or <code> dx1 dy1 dx2 dy2 ...
            coord_list = get_abs_coords(code,parse_coord_list(svg_seq[i+1]),last_coord)
            for x, y in coord_list:
                path_code = SVG_CODE_MAP[code]
                path_codes.append(path_code)
                path_verts.append((x,y))
                if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            if code == 'M' or code == 'm':
                start_coord[:] = last_coord
            i += 2
            continue

        if code in 'HhVv': # <code> x1 x2 ...
            number_list = get_abs_coords(code,parse_number_list(svg_seq[i+1]),last_coord)
            #print(number_list)
            for x,y in number_list:
                path_code = SVG_CODE_MAP[code]
                path_codes.append(path_code)
                path_verts.append((x,y))
                if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            i += 2
            continue

        if code in 'Zz': # Z or z
            x, y = start_coord[0],start_coord[1] # dummy
            path_code = SVG_CODE_MAP[code]
            path_codes.append(path_code)
            path_verts.append((x, y)) # dummy
            if trace_codes: print(('trace',i,'code',code,'path_code',SVG_CODE_NAME_MAP[path_code],'path_vert',x,y),file=sys.stderr)
            last_coord[:] = start_coord
            i += 1
            continue

        # if code == 'A': # A rx ry a f1 f2 x y
        #     pass

        # if code == 'a': # a rx ry a f1 f2 dx dy
        #     pass

        # if code == '\n':
        #     i += 1
        #     continue # skip

        raise RuntimeError(('unknown code',code))

    return path_verts, path_codes


