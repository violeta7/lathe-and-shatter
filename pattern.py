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
import numpy as np
from scipy.spatial import Voronoi
from clipper import liang_barsky_clipper


def is_ccw(x0, y0, x1, y1, x2, y2):
    """
    path-is-counter-clockwise
    https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order#1165943
    """
    sum_over_edges = (x1 - x0) * (y1 + y0) + \
                     (x2 - x1) * (y2 + y1) + \
                     (x0 - x2) * (y0 + y2)

    return sum_over_edges < 0


def create_pattern(num_cells):
    """
    create cylinderical voronoi and line segments
    """

    xmin, ymin, xmax, ymax = 0.0, 0.0, 1.0, 1.0
    width = xmax - xmin

    points = np.random.uniform([xmin,ymin],[xmax,ymax],size=[num_cells,2])
    points_mirrored = np.concatenate([points,points + [-width, 0.0],points + [width, 0.0],],axis=0)

    vor = Voronoi(points_mirrored)

    # 모든 ridge_vertices 에 대해서 liang_barsky_clipper 적용 ==> clipped_linesegs

    lineseg_dict = dict()
    c_point_linesegs = [[] for _ in range(num_cells)]

    for i, xy in enumerate(vor.points):

        # canonical point index
        if i >= 2 * num_cells:
            c_i = i - 2 * num_cells
        elif i >= num_cells:
            c_i = i - num_cells
        else:
            c_i =i

        vs = list(vor.regions[vor.point_region[i]])

        evs = vs + [vs[0]]
        for j in range(len(vs)):
            v1, v2 = evs[j:j+2]
            if v1 >= 0 and v2 >= 0:
                if v1 == v2:
                    print('*** v1 == v2',i,j,v1,v2,vor.regions[vor.point_region[i]])

                # normalized v1, v2 for dict index
                rev = False
                if v1 > v2:
                    v1, v2, rev = v2, v1, True

                # check if counter-clockwise
                x0, y0 = xy
                x1, y1 = vor.vertices[v1]
                x2, y2 = vor.vertices[v2]

                ccw = is_ccw(x0, y0, x1, y1, x2, y2)
                if rev:
                    ccw = not ccw

                if (v1, v2) not in lineseg_dict:
                    nx1, ny1, nx2, ny2, valid = liang_barsky_clipper(xmin, ymin, xmax, ymax, x1, y1, x2, y2)
                    if valid:
                        x1_wrapped = (x1 < 0.0 or x1 > 1.0)
                        x2_wrapped = (x2 < 0.0 or x2 > 1.0)
                        y1_clipped = (y1 < 0.0 or y1 > 1.0)
                        y2_clipped = (y2 < 0.0 or y2 > 1.0)
                        lineseg_dict[(v1, v2)] = [[nx1, ny1], [nx2, ny2], x1_wrapped, x2_wrapped, y1_clipped, y2_clipped]

                if (v1, v2) in lineseg_dict:
                    if not ( rev ^ ccw ):
                        v2, v1 = v1, v2
                    assert (v1, v2) not in c_point_linesegs[c_i]
                    c_point_linesegs[c_i].append((v1, v2))

    return vor, lineseg_dict, c_point_linesegs


import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_pattern(voronoi, lineseg_dict, c_point_linesegs, selections=None, ax=None):

    xmin, ymin, xmax, ymax = 0.0, 0.0, 1.0, 1.0

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    ax.plot([xmin,xmax,xmax,xmin,xmin],[ymin,ymin,ymax,ymax,ymin])

    if selections is None:
        selections = list(range(len(voronoi.points)//3))

    for i in selections:
        x, y = voronoi.points[i]
        ax.text(x,y,str(i))

        num_segs = len(c_point_linesegs[i])

        for j, seg in enumerate(c_point_linesegs[i]):

            v1, v2 = seg

            if (v1,v2) in lineseg_dict:
                p1, p2, _, _, _, _ = lineseg_dict[(v1, v2)]
            elif (v2,v1) in lineseg_dict:
                p2, p1, _, _, _, _ = lineseg_dict[(v2, v1)]
            else:
                assert 0

            x1, y1 = p1
            x2, y2 = p2

            if j == 0: # check if first clipped
                ax.scatter([x1],[y1],c='r')

            ax.quiver([x1],[y1],[x2-x1],[y2-y1],scale_units='xy',angles='xy',scale=1,color='k',alpha=0.1+0.8*float(j)/num_segs)


from scipy.spatial import voronoi_plot_2d

def save_pattern_png(voronoi, figname):
    fig = plt.figure(frameon=False)
    fig.set_size_inches(11.5,11.5)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    voronoi_plot_2d(voronoi, ax=ax)
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.set_xlim([0.0, 1.0])
    plt.savefig(figname)

import json

def save_pattern_json(voronoi, filename):
    n_groups = len(voronoi.points) // 3
    voronoi_group = np.arange(len(voronoi.points))
    voronoi_group[n_groups:n_groups*2] -= n_groups
    voronoi_group[n_groups*2:] -= n_groups * 2
    voronoi_shatter = {
        'num_groups': n_groups,
        'point_group': voronoi_group.tolist(),
        'point': voronoi.points.tolist(),
    }
    with open(filename,'w') as f:
        json.dump(voronoi_shatter,f)

def load_pattern_json(filename):
    with open(filename,'r') as f:
        voronoi_shatter = json.load(f)

    num_groups = voronoi_shatter['num_groups']
    voronoi_points = np.array(voronoi_shatter['point'])
    voronoi_group = np.array(voronoi_shatter['point_group'])
    return num_groups, voronoi_points, voronoi_group


def find_voronoi_group(uvcoords, voronoi_points, voronoi_group):
    assert uvcoords.ndim == 2
    assert uvcoords.shape[1] == 2
    uvcoords = uvcoords.reshape([-1,1,2])
    offs = uvcoords - voronoi_points # shape (-1, N, 2)
    dists = np.linalg.norm(offs,axis=-1) # shape (-1, N)
    center = np.argmin(dists, axis=-1) # get nearest center, shape (-1)
    group = voronoi_group[center]
    return group

